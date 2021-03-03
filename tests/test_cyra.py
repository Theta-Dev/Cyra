import unittest

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

    def test_remove(self):
        exp_res = [('key1', 'val1'), ('key2.1', 'val2.1'), ('key2.2', 'val2.2'), ('key3', 'val3')]
        res = []

        cyra.core.DictUtil.remove(self.d, lambda key, value: key.startswith('__'))
        cyra.core.DictUtil.iterate(self.d, lambda key, value: res.append((key, value)))
        self.assertEqual(exp_res, res)


class TestConfigBuilder(unittest.TestCase):
    def test_build_config(self):
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
        builder.pop()

        builder.comment('Cyra says goodbye')
        builder.define('msg2', 'Bye bye, World')

        cfg = builder.build()

        print(cfg.to_toml())
