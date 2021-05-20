import unittest
import copy
from collections import OrderedDict

import tomlkit
import os
import shutil

import tests
import cyra
import cyra.core


class TestDictUtil(unittest.TestCase):
    def setUp(self):
        # Test dictionary
        self.d = {
            'key1': 'val1',
            'key2': {
                'key2.1': 'val2.1',
                'key2.2': 'val2.2'
            },
            'key3': 'val3',
            '__int': 'valInt'
        }

    def test_iterate(self):
        exp_res = {('key1', 'val1'), ('key2.1', 'val2.1'), ('key2.2', 'val2.2'), ('key3', 'val3'), ('__int', 'valInt')}
        res = set()

        cyra.core.DictUtil.iterate(self.d, lambda key, value: res.add((key, value)))
        self.assertEqual(exp_res, res)

    def test_get_elememt(self):
        res = cyra.core.DictUtil.get_element(self.d, ('key2', 'key2.2'))
        self.assertEqual('val2.2', res)

        self.assertIsNone(cyra.core.DictUtil.get_element(self.d, ('key2', 'keyX')))

        self.assertRaises(ValueError, cyra.core.DictUtil.get_element, self.d, tuple())

        self.assertIsNone(cyra.core.DictUtil.get_element(self.d, ('key2', 'keyX', 'keyY')))

    def test_set_element(self):
        exp_res = copy.deepcopy(self.d)
        exp_res['key2']['key2.2'] = 'val_mod'

        cyra.core.DictUtil.set_element(self.d, ('key2', 'key2.2'), 'val_mod')
        self.assertEqual(exp_res, self.d)

        exp_res['key_mod'] = {}
        exp_res['key_mod']['key_m1'] = 'val_mod1'

        cyra.core.DictUtil.set_element(self.d, ('key_mod', 'key_m1'), 'val_mod1')
        self.assertEqual(exp_res, self.d)

        self.assertRaises(ValueError, cyra.core.DictUtil.set_element, self.d, tuple(), 'x')


class TestConfigBuilder(unittest.TestCase):
    def test_build_config(self):
        exp_res = """msg = "Hello World" # Cyra says hello
msg2 = "Bye bye, World" # Cyra says goodbye

[DATABASE] # SQL Database settings
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
password = "my_secret_password"
enable = true # DB connection enabled
"""

        builder = cyra.core.ConfigBuilder()

        builder.comment('Cyra says hello')
        builder.define('msg', 'Hello World')

        builder.comment('SQL Database settings')
        builder.push('DATABASE')
        builder.comment('DB server address')
        builder.define('server', '192.168.1.1')
        builder.comment('SQL port (default: 1443)')
        builder.define('port', 1443)
        builder.comment('Credentials')
        builder.define('username', 'admin')
        builder.define('password', 'my_secret_password')
        builder.comment('DB connection enabled')
        builder.define('enable', True)
        builder.pop()

        builder.comment('Cyra says goodbye')
        builder.define('msg2', 'Bye bye, World')

        cfg = cyra.Config('', builder)
        self.assertEqual(exp_res, cfg.export_toml())

    def test_build_complex_config(self):
        exp_res = """msg = "Hello World" # Cyra says hello

[DATABASE] # SQL Database settings
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
password = "my_secret_password"

[SERVERS] # Servers to be monitored
[SERVERS.alpha]
ip = "10.0.0.1" # Server IP address
enable = true # Set to false to disable server access
priority = 1 # Server priority
users = ["ThetaDev", "Cyra"] # Users to be handled

[SERVERS.beta]
ip = "10.0.0.2" # Server IP address
enable = false # Set to false to disable server access
priority = 2 # Server priority
users = ["ThetaDev"] # Users to be handled

[DICT] # Arbitrary dictionary
key1 = "V1"
key2 = "V2"
key3 = 3

[DICT.keyA]
keyA1 = "VA1"
keyA2 = true

[DICT.keyB]
keyB1 = "VB1"
keyB2 = ["VB2a", "VB2b"]
"""

        builder = cyra.core.ConfigBuilder()

        builder.comment('Cyra says hello')
        builder.define('msg', 'Hello World')

        builder.comment('SQL Database settings')
        builder.push('DATABASE')
        builder.comment('DB server address')
        builder.define('server', '192.168.1.1')
        builder.comment('SQL port (default: 1443)')
        builder.define('port', 1443)
        builder.comment('Credentials')
        builder.define('username', 'admin')
        builder.define('password', 'my_secret_password')
        builder.comment('DB connection enabled')
        builder.pop()

        builder.comment('Servers to be monitored')
        builder.push('SERVERS')

        builder.push('alpha')
        builder.comment('Server IP address')
        builder.define('ip', '10.0.0.1')
        builder.comment('Set to false to disable server access')
        builder.define('enable', True)
        builder.comment('Server priority')
        builder.define('priority', 1)
        builder.comment('Users to be handled')
        builder.define('users', ['ThetaDev', 'Cyra'])
        builder.pop()

        builder.push('beta')
        builder.comment('Server IP address')
        builder.define('ip', '10.0.0.2')
        builder.comment('Set to false to disable server access')
        builder.define('enable', False)
        builder.comment('Server priority')
        builder.define('priority', 2)
        builder.comment('Users to be handled')
        builder.define('users', ['ThetaDev'])
        builder.pop(2)

        builder.comment('Arbitrary dictionary')
        # Use ordered dict to keep same order between Python versions
        _xdict = OrderedDict()
        _xdict['key1'] = 'V1'
        _xdict['key2'] = 'V2'
        _xdict['key3'] = 3
        _xdict['keyA'] = OrderedDict([('keyA1', 'VA1'), ('keyA2', True)])
        _xdict['keyB'] = OrderedDict([('keyB1', 'VB1'), ('keyB2', ['VB2a', 'VB2b'])])
        builder.define('DICT', _xdict)

        cfg = cyra.Config('', builder)
        self.assertEqual(exp_res, cfg.export_toml())

    def test_build_faulty_config(self):
        builder = cyra.core.ConfigBuilder()
        builder.define('key1', 'val1')

        # Try to push / define value with existing key
        self.assertRaises(ValueError, builder.push, 'key1')
        self.assertRaises(ValueError, builder.define, 'key1', 'val2')

        # Invalid keys
        self.assertRaises(ValueError, builder.define, 'key1.1', 'valX')
        self.assertRaises(ValueError, builder.define, '', 'valX')

        # Try to pop more elements than active path length
        self.assertRaises(ValueError, builder.pop)


class TestConfigValue(unittest.TestCase):
    def test_config_value(self):
        # Default value
        cval = cyra.core.ConfigValue('mycomment', 'val1', validator=lambda x: x != 'forbidden')
        self.assertEqual('val1', cval.val)

        # Modify value
        cval.val = 'val2'
        self.assertEqual('val2', cval.val)

        # Value casting
        cval.val = 256
        self.assertEqual('256', cval.val)

        # Forbidden value
        cval.val = 'forbidden'
        self.assertEqual('val1', cval.val)

        self.assertEqual('val1', str(cval))
        self.assertEqual(repr('val1'), repr(cval))


class Cfg(cyra.Config):
    """DSTRING: Begin"""

    builder = cyra.core.ConfigBuilder()

    builder.comment('Cyra says hello')
    MSG = builder.define('msg', 'Hello World')

    builder.docstring('DSTRING: Database settings')

    builder.comment('SQL Database settings')
    builder.push('DATABASE')
    builder.comment('DB server address')
    SERVER = builder.define('server', '192.168.1.1')
    builder.comment('SQL port (default: 1443)')
    PORT = builder.define('port', 1443)
    builder.comment('Credentials')
    USERNAME = builder.define('username', 'admin')
    PASSWORD = builder.define('password', 'my_secret_password')
    builder.comment('DB connection enabled')
    ENABLE = builder.define('enable', True)
    builder.pop()

    builder.docstring('DSTRING: Goodbye')

    builder.comment('Cyra says goodbye')
    MSG2 = builder.define('msg2', 'Bye bye, World')


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = Cfg('')

    def test_set_toml_entry(self):
        toml = tomlkit.document()
        cyra.core.Config._set_toml_entry(toml, ('key1',), cyra.core.ConfigValue('Comment1', 'val1'))
        cyra.core.Config._set_toml_entry(toml, ('key2', 'key2.1'), cyra.core.ConfigValue('Comment2', 'val2'))

        exp_res = """key1 = "val1" # Comment1

[key2]
"key2.1" = "val2" # Comment2
"""
        self.assertEqual(exp_res, tomlkit.dumps(toml))

        self.assertRaises(ValueError, cyra.core.Config._set_toml_entry, toml, tuple(),
                          cyra.core.ConfigValue('Comment1', 'val1'))

    def test_load_dict(self):
        dic = {
            'msg': 'Okay? Okay.',
            'DATABASE': {
                'password': 'very_secret_password'
            }
        }

        self.cfg._load_dict(dic)

        self.assertEqual('Okay? Okay.', self.cfg.MSG)
        self.assertEqual('very_secret_password', self.cfg.PASSWORD)

    def test_load_export_toml(self):
        toml_str = """
msg = "Okay? Okay." # Are we ok?

[DATABASE] # SQL Database settings
password = "very_secret_password"
"""
        exp_res = """
msg = "Okay? Okay." # Are we ok?
msg2 = "Bye bye, World" # Cyra says goodbye

[DATABASE] # SQL Database settings
password = "very_secret_password"
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
enable = true # DB connection enabled
"""
        self.cfg.load_toml(toml_str)

        self.assertEqual('Okay? Okay.', self.cfg.MSG)
        self.assertEqual('very_secret_password', self.cfg.PASSWORD)

        self.cfg.load_toml(toml_str)

        self.assertEqual(exp_res, self.cfg.export_toml())

    def test_load_flat_dict(self):
        flat_dict = {
            ('msg',): 'Okay? Okay.',
            ('DATABASE', 'password'): 'very_secret_password'
        }

        self.cfg.load_flat_dict(flat_dict)

        self.assertEqual('Okay? Okay.', self.cfg.MSG)
        self.assertEqual('very_secret_password', self.cfg.PASSWORD)

    def test_load_file(self):
        # Copy fresh config file into tmp folder
        self.tmpdir = tests.tmpdir()
        cfg_file = os.path.join(self.tmpdir.name, 'testcfg.toml')
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'testcfg_import.toml'), cfg_file)

        self.cfg._file = cfg_file
        self.cfg.load_file()

        self.assertEqual('Okay? Okay.', self.cfg.MSG)
        self.assertEqual('very_secret_password', self.cfg.PASSWORD)

        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'testcfg_writeback.toml'), cfg_file)

    def test_gen_file(self):
        self.tmpdir = tests.tmpdir()
        cfg_file = os.path.join(self.tmpdir.name, 'testcfg.toml')

        self.cfg._file = cfg_file
        self.cfg.load_file()

        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'testcfg.toml'), cfg_file)

    def test_export_toml(self):
        toml_str = """
msg = "I am Cyra" # Hello, I am here
"""
        exp_res = """
msg = "Okay? Okay." # Hello, I am here
msg2 = "Bye bye, World" # Cyra says goodbye

[DATABASE] # SQL Database settings
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
password = "very_secret_password"
enable = false # DB connection enabled
"""
        self.cfg.load_toml(toml_str)

        self.cfg.MSG = 'Okay? Okay.'
        self.cfg.PASSWORD = 'very_secret_password'
        self.cfg.ENABLE = False

        new_toml_str = self.cfg.export_toml()
        self.assertEqual(exp_res, new_toml_str)

    def test_doc_blocks(self):
        doc_blocks = self.cfg.get_docblocks()

        docstrings = [
            'DSTRING: Begin',
            'DSTRING: Database settings',
            'DSTRING: Goodbye',
        ]

        tomlstrings = [
            'msg = "Hello World" # Cyra says hello',
            '''
[DATABASE] # SQL Database settings
server = "192.168.1.1" # DB server address
port = 1443 # SQL port (default: 1443)
username = "admin" # Credentials
password = "my_secret_password"
enable = true # DB connection enabled
            ''',
            'msg2 = "Bye bye, World" # Cyra says goodbye',
        ]

        for i, b in enumerate(doc_blocks):
            self.assertEqual(docstrings[i], b[0])
            self.assertEqual(tomlstrings[i].strip(), b[1].strip())
