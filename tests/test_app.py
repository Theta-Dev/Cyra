import unittest
import os
import shutil

import tests
import cyra


class Cfg:
    builder = cyra.ConfigBuilder()

    builder.comment('Cyra says hello')
    msg = builder.define('msg', 'Hello World')

    builder.comment('SQL Database settings')
    builder.push('DATABASE')
    builder.comment('DB server address')
    server = builder.define('server', '192.168.1.1')
    builder.comment('SQL port (default: 1443)')
    port = builder.define('port', 1443)
    builder.comment('Credentials')
    user = builder.define('username', 'admin')
    pwd = builder.define('password', 'my_secret_password')
    builder.comment('DB connection enabled')
    builder.pop()

    builder.comment('Servers to be monitored')
    builder.push('SERVERS')

    builder.push('alpha')
    builder.comment('Server IP address')
    ip_a = builder.define('ip', '10.0.0.1')
    builder.comment('Set to false to disable server access')
    en_a = builder.define('enable', True)
    builder.comment('Server priority')
    prio_a = builder.define('priority', 1)
    builder.comment('Users to be handled')
    users_a = builder.define('users', ['ThetaDev', 'Cyra'])
    builder.pop()

    builder.push('beta')
    builder.comment('Server IP address')
    ip_b = builder.define('ip', '10.0.0.2')
    builder.comment('Set to false to disable server access')
    en_b = builder.define('enable', False)
    builder.comment('Server priority')
    prio_b = builder.define('priority', 2)
    builder.comment('Users to be handled')
    users_b = builder.define('users', ['ThetaDev'])
    builder.pop(2)

    builder.comment('Arbitrary dictionary')
    xdict = builder.define('DICT', {
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

    def __init__(self, cfg_file):
        self.cyraconf = Cfg.builder.build(cfg_file)


class TestApplication(unittest.TestCase):
    def setUp(self) -> None:
        tests.clear_tmp_folder()
        self.cfg_file = os.path.join(tests.DIR_TMP, 'appcfg.toml')

    def test_gen_file(self):
        cfg = Cfg(self.cfg_file)
        cfg.cyraconf.load_file()
        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'appcfg.toml'), self.cfg_file)

    def test_load_config(self):
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'appcfg_import.toml'), self.cfg_file)

        cfg = Cfg(self.cfg_file)
        cfg.cyraconf.load_file()

        self.assertEqual('I am Cyra', cfg.msg)
        self.assertEqual(1234, cfg.port)
        self.assertEqual('127.0.0.1', cfg.ip_b)
        self.assertEqual(True, cfg.en_b)

    def test_modify_config(self):
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'appcfg.toml'), self.cfg_file)

        cfg = Cfg(self.cfg_file)
        cfg.cyraconf.load_file()

        cfg.msg = 'I am Cyra'
        cfg.port = 1234
        cfg.ip_b = '127.0.0.1'
        cfg.en_b = True

        cfg.cyraconf.save_file()
        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'appcfg_modify.toml'), self.cfg_file)
