from collections import OrderedDict
import copy
import tomlkit


class DictUtil:
    @staticmethod
    def iterate(d: dict, fun):
        """
        Iterates through a nested dictionary, calling the function ``fun`` on every key/value.
        :param d: Dictionary
        :param fun: Function/Lambda ``fun(key, value)``
        """
        for key, value in d.items():
            if isinstance(value, dict):
                DictUtil.iterate(value, fun)
            else:
                fun(key, value)

    @staticmethod
    def get_element(d: dict, path: tuple):
        """
        Gets element from a nested dictionary
        :param d: Dictionary
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :return: element or None
        :raise ValueError: if Path is empty
        """
        if len(path) == 0:
            raise ValueError('Path length cant be 0')
        elif len(path) == 1:
            return d.get(path[0])
        elif d.get(path[0]):
            return DictUtil.get_element(d[path[0]], path[1:])
        return None

    @staticmethod
    def set_element(d: dict, path: tuple, value, default_dict=None):
        """
        Sets element in a nested dictionary, creating additional sub-dictionaries if necessary
        :param d: Dictionary
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :param value: Value to be set
        :param default_dict: Empty dictionary to be created if missing (default: ``dict()``)
        :raise ValueError: if Path is empty
        """
        if default_dict is None:
            default_dict = dict()

        if len(path) == 0:
            raise ValueError('Path length cant be 0')
        elif len(path) == 1:
            d[path[0]] = value
        else:
            DictUtil.set_element(d.setdefault(path[0], default_dict), path[1:], value, default_dict)


class ConfigEntry:
    def __init__(self, comment: str = ''):
        self.comment = comment


class ConfigValue(ConfigEntry):
    def __init__(self, comment: str = '', default=''):
        super().__init__(comment)
        self.default = default
        self._value = default

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = type(self.default)(value)

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = value


class Config:
    def __init__(self, config: OrderedDict):
        self._config = config

    @staticmethod
    def _set_toml_entry(toml, path, entry: ConfigEntry):
        if len(path) == 0:
            raise ValueError('Path length cant be 0')
        elif len(path) == 1:
            if isinstance(entry, ConfigValue):
                toml.add(path[0], entry.value)
            else:
                toml.add(path[0], tomlkit.table())

            if entry.comment:
                toml[path[0]].comment(entry.comment)
        else:
            if path[0] not in toml:
                toml.add(path[0], tomlkit.table())

            Config._set_toml_entry(toml[path[0]], path[1:], entry)

    def to_toml(self):
        toml = tomlkit.document()

        for path, entry in self._config.items():
            Config._set_toml_entry(toml, path, entry)

        return tomlkit.dumps(toml)

    def _load_dict(self, cfg_dict: dict, wb_fun=None):
        n_writeback = 0

        for path in self._config.keys():
            entry = self._config[path]
            if not isinstance(entry, ConfigValue):
                continue

            new_value = DictUtil.get_element(cfg_dict, path)

            # Import value if present in config dict
            if new_value:
                entry.value = new_value

            # Insert default value to config dict if value is not present there
            elif callable(wb_fun):
                wb_fun(path, entry)
                n_writeback += 1
        return n_writeback

    def load_dict(self, cfg_dict: dict, writeback=False):
        return self._load_dict(cfg_dict,
                               lambda path, entry:
                               DictUtil.set_element(cfg_dict, path, entry.default) if writeback else None)

    def load_toml(self, toml_str: str, writeback=False):
        toml = tomlkit.loads(toml_str)

        n_writeback = self._load_dict(toml.value,
                                      lambda path, entry:
                                      Config._set_toml_entry(toml, path, entry) if writeback else None)

        if n_writeback:
            print('Inserted %d new items into config file' % n_writeback)
            return tomlkit.dumps(toml)
        return None


class ConfigBuilder:
    def __init__(self):
        # Config dict: Key(tuple) -> ConfigEntry
        self._config = OrderedDict()

        # Temporary comment (will be added to next entry)
        self._tmp_comment = ''

        # Currently active path
        self._active_path = tuple()

    @staticmethod
    def _check_key(key):
        if not key:
            raise ValueError('Key must not be empty.')

    def define(self, key: str, default) -> ConfigValue:
        self._check_key(key)
        npath = self._active_path + (key,)

        if npath in self._config:
            raise ValueError('Attempted to set existing entry at ' + str(npath))

        cfg_value = ConfigValue(self._tmp_comment, default)
        self._config[npath] = cfg_value
        self._tmp_comment = ''
        return cfg_value

    def comment(self, comment: str):
        self._tmp_comment = comment

    def push(self, key: str):
        self._check_key(key)
        self._active_path += (key,)

        if self._active_path not in self._config:
            self._config[self._active_path] = ConfigEntry(self._tmp_comment)
        self._tmp_comment = ''

    def pop(self, n=1):
        if n > len(self._active_path):
            raise ValueError('Attempted to pop %d elements when whe only had %d' % (n, len(self._active_path)))

        self._active_path = self._active_path[:-n]

    def build(self) -> Config:
        # Copy built config with all its values into the new Config object
        new_config = copy.deepcopy(self._config)

        return Config(new_config)
