import os
import unittest
import shutil
from unittest.mock import patch

from bs4 import BeautifulSoup
from sphinx.testing.util import SphinxTestApp
from sphinx.testing.util import path as sphinx_path

import tests


class TestDocs(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tests.tmpdir()
        self.input_dir = os.path.join(self.tmpdir.name, 'testdocs')
        shutil.copytree(tests.DIR_TESTDOCS, self.input_dir)

        self.app = SphinxTestApp(srcdir=sphinx_path(self.input_dir))
        self.output_dir = os.path.join(self.input_dir, '_build', 'html')

    def tearDown(self):
        self.app.cleanup()

    def test_cyradoc(self):
        with patch('cyra.cyradoc.logger.error') as mock_logger:
            self.app.build()

        # Test doc should produce 4 warnings
        warnings = [
            'Cyradoc path must have the format <Module>.<Class>',
            'Cyradoc could not find module nomodule',
            'Cyradoc could not find class NoClass in module tests.test_core',
            'Class tests.test_core.TestConfig is not a Cyradoc class',
        ]
        for i, call in enumerate(mock_logger.call_args_list):
            self.assertEqual(warnings[i], call[0][0])

        output_file = os.path.join(self.output_dir, 'index.html')
        with open(output_file, 'r', encoding='utf-8') as f:
            html_doc = f.read()

        soup = BeautifulSoup(html_doc, 'html.parser')
        body = soup.find(role='main')

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
