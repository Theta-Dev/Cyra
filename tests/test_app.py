import unittest
import os
import shutil
from collections import OrderedDict

import tests
import cyra

# noinspection PyUnresolvedReferences
from tests import tmpdir


class Cfg(cyra.Config):
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
    dben = builder.define('enabled', True)
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
    users_a = builder.define('users', ['ThetaDev', 'Clary'])
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

    # Use ordered dict to keep same order between Python versions
    _xdict = OrderedDict()
    _xdict['key1'] = 'V1'
    _xdict['key2'] = 'V2'
    _xdict['key3'] = 3
    _xdict['keyA'] = OrderedDict([('keyA1', 'VA1'), ('keyA2', True)])
    _xdict['keyB'] = OrderedDict([('keyB1', 'VB1'), ('keyB2', ['VB2a', 'VB2b'])])

    xdict = builder.define('DICT', _xdict)

    builder.comment('Value to be validated')
    validatable = builder.define('validatable', 'fallback', lambda x: x != 'forbidden')


class TestApplication(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tests.tmpdir()
        self.cfg_file = os.path.join(self.tmpdir.name, 'appcfg.toml')

    def test_gen_file(self):
        cfg = Cfg(self.cfg_file)
        cfg.load_file()
        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'appcfg.toml'), self.cfg_file)

    def test_load_config(self):
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'appcfg_import.toml'), self.cfg_file)

        cfg = Cfg(self.cfg_file)
        cfg.load_file()

        self.assertEqual('I am Cyra', cfg.msg)
        self.assertEqual(1234, cfg.port)
        self.assertEqual('127.0.0.1', cfg.ip_b)
        self.assertEqual(True, cfg.en_b)

    def test_modify_config(self):
        shutil.copyfile(os.path.join(tests.DIR_TESTFILES, 'appcfg.toml'), self.cfg_file)

        cfg = Cfg(self.cfg_file)
        cfg.load_file()

        cfg.msg = 'I am Cyra'
        cfg.port = 1234
        cfg.ip_b = '127.0.0.1'
        cfg.en_b = True

        cfg.save_file()
        tests.assert_files_equal(self, os.path.join(tests.DIR_TESTFILES, 'appcfg_modify.toml'), self.cfg_file)

    def test_multiple_instances(self):
        cfg1 = Cfg('')
        cfg2 = Cfg('')

        cfg1.msg = 'Cyra number one'
        cfg2.msg = 'Cyra number two'

        self.assertEqual('Cyra number one', cfg1.msg)
        self.assertEqual('Cyra number two', cfg2.msg)

    def test_validator(self):
        cfg = Cfg('')

        cfg.validatable = 'NewValue'
        self.assertEqual('NewValue', cfg.validatable)

        cfg.validatable = 'forbidden'
        self.assertEqual('fallback', cfg.validatable)
