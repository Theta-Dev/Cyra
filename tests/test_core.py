import unittest
import copy
import tomlkit
import os
import shutil

import tests
import cyra
import cyra.core


class TestDictUtil(unittest.TestCase):
    def setUp(self) -> None:
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
        exp_res = [('key1', 'val1'), ('key2.1', 'val2.1'), ('key2.2', 'val2.2'), ('key3', 'val3'), ('__int', 'valInt')]
        res = []

        cyra.core.DictUtil.iterate(self.d, lambda key, value: res.append((key, value)))
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

        cfg = builder.build('')
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
        builder.define('DICT', {
            'key1': 'V1',
            'key2': 'V2',
            'key3': 3,
            'keyA': {
                'keyA1': 'VA1',
                'keyA2': True
            },
            'keyB': {
                'keyB1': 'VB1',
                'keyB2': ['VB2a', 'VB2b']
            }
        })

        cfg = builder.build('')
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
        cval = cyra.core.ConfigValue('mycomment', 'val1')
        self.assertEqual('val1', cval.val)

        # Modify value
        cval.val = 'val2'
        self.assertEqual('val2', cval.val)

        # Value casting
        cval.val = 256
        self.assertEqual('256', cval.val)

        # Repr / Str
        self.assertEqual("'256'", repr(cval))
        self.assertEqual('256', str(cval))

    def test_config_value_get(self):
        tst_cfg = cyra.core.Config(None, '')

        class Cfg:
            OPT = cyra.core.ConfigValue('mycomment', 'val1')
            OPT._config = tst_cfg

        cfg = Cfg()
        self.assertEqual('val1', cfg.OPT)
        self.assertFalse(tst_cfg._modified)

        cfg.OPT = 'val2'
        self.assertEqual('val2', cfg.OPT)
        self.assertTrue(tst_cfg._modified)


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = cyra.core.ConfigBuilder()

        self.builder.comment('Cyra says hello')
        self.MSG = self.builder.define('msg', 'Hello World')

        self.builder.comment('SQL Database settings')
        self.builder.push('DATABASE')
        self.builder.comment('DB server address')
        self.SERVER = self.builder.define('server', '192.168.1.1')
        self.builder.comment('SQL port (default: 1443)')
        self.PORT = self.builder.define('port', 1443)
        self.builder.comment('Credentials')
        self.USERNAME = self.builder.define('username', 'admin')
        self.PASSWORD = self.builder.define('password', 'my_secret_password')
        self.builder.comment('DB connection enabled')
        self.ENABLE = self.builder.define('enable', True)
        self.builder.pop()

        self.builder.comment('Cyra says goodbye')
        self.MSG2 = self.builder.define('msg2', 'Bye bye, World')

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
        cfg = self.builder.build('')
        dic = {
            'msg': 'Okay? Okay.',
            'DATABASE': {
                'password': 'very_secret_password'
            }
        }

        cfg._load_dict(dic)

        self.assertEqual('Okay? Okay.', self.MSG.val)
        self.assertEqual('very_secret_password', self.PASSWORD.val)

    def test_load_export_toml(self):
        cfg = self.builder.build('')
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
        cfg.load_toml(toml_str)

        self.assertEqual('Okay? Okay.', self.MSG.val)
        self.assertEqual('very_secret_password', self.PASSWORD.val)

        cfg.load_toml(toml_str)

        self.assertEqual(exp_res, cfg.export_toml())

    def test_load_flat_dict(self):
        cfg = self.builder.build('')
        flat_dict = {
            ('msg',): 'Okay? Okay.',
            ('DATABASE', 'password'): 'very_secret_password'
        }

        cfg.load_flat_dict(flat_dict)

        self.assertEqual('Okay? Okay.', self.MSG.val)
        self.assertEqual('very_secret_password', self.PASSWORD.val)

    def test_load_file(self):
        # Copy fresh config file into tmp folder
        tests.clear_tmp_folder()
        cfg_file = os.path.join(tests.DIR_TMP, 'testcfg.toml')
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'testcfg_import.toml'), cfg_file)

        cfg = self.builder.build(cfg_file)
        cfg.load_file()

        self.assertEqual('Okay? Okay.', self.MSG.val)
        self.assertEqual('very_secret_password', self.PASSWORD.val)

        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'testcfg_writeback.toml'), cfg_file)

    def test_gen_file(self):
        tests.clear_tmp_folder()
        cfg_file = os.path.join(tests.DIR_TMP, 'testcfg.toml')

        cfg = self.builder.build(cfg_file)
        cfg.load_file()

        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'testcfg.toml'), cfg_file)

    def test_export_toml(self):
        cfg = self.builder.build('')

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
        cfg.load_toml(toml_str)

        self.MSG.val = 'Okay? Okay.'
        self.PASSWORD.val = 'very_secret_password'
        self.ENABLE.val = False

        new_toml_str = cfg.export_toml()
        self.assertEqual(exp_res, new_toml_str)
