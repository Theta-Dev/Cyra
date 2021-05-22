import os
import unittest
import shutil
from unittest.mock import patch

from bs4 import BeautifulSoup
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.util import path as sphinx_path

import tests
from tests.test_core import Cfg


class TestDocs(unittest.TestCase):
    tmpdir = None
    app = None
    input_dir = None
    output_dir = None
    mock_logger = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tests.tmpdir()
        cls.input_dir = os.path.join(cls.tmpdir.name, 'testdocs')
        shutil.copytree(tests.DIR_TESTDOCS, cls.input_dir)

        cls.app = SphinxTestApp(srcdir=sphinx_path(cls.input_dir))
        cls.output_dir = os.path.join(cls.input_dir, '_build', 'html')

        with patch('cyra.cyradoc.logger.error') as cls.mock_logger:
            cls.app.build()

    @classmethod
    def tearDownClass(cls):
        cls.app.cleanup()
        cls.tmpdir.cleanup()

    def test_warnings(self):
        # Test doc should produce 4 warnings
        warnings = [
            'Cyradoc path must have the format <Module>.<Class>',
            'Cyradoc could not find module nomodule',
            'Cyradoc could not find class NoClass in module tests.test_core',
            'Class tests.test_core.TestConfig is not a Cyradoc class',
        ]
        for i, call in enumerate(self.mock_logger.call_args_list):
            self.assertEqual(warnings[i], call[0][0])

    def parse_file(self, name):
        output_file = os.path.join(self.output_dir, name)
        with open(output_file, 'r', encoding='utf-8') as f:
            html_doc = f.read()

        soup = BeautifulSoup(html_doc, 'html.parser')
        return soup.find(role='main')

    def test_cyradoc(self):
        body = self.parse_file('index.html')

        exp_docstrings = ['DSTRING: Begin', 'DSTRING: Database settings', 'DSTRING: Goodbye']
        docstrings = [n.getText() for n in body.findAll('p')]
        self.assertEqual(exp_docstrings, docstrings)

        exp_blocks = [
            'msg = "Hello World" # Cyra says hello',
            '''[DATABASE] # SQL Database settings
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
password = "my_secret_password"
enable = true # DB connection enabled''',
            'msg2 = "Bye bye, World" # Cyra says goodbye',
        ]
        blocks = [n.getText().strip() for n in body.findAll('pre')]
        self.assertEqual(exp_blocks, blocks)

    def test_no_docstrings(self):
        body = self.parse_file('no_docstrings.html')

        exp_toml = Cfg('').export_toml().strip('\n')
        toml = body.getText().strip('\n')

        self.assertEqual(exp_toml, toml)

    def test_errors(self):
        body = self.parse_file('errors.html')

        content = body.getText().strip('\n')
        self.assertEqual('', content)
