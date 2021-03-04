from typing import Optional, Dict, Tuple, Callable, Any
from collections import OrderedDict
import os
import copy
import logging
import tomlkit
from tomlkit.toml_document import TOMLDocument


class DictUtil:
    """A few useful functions for handling nested dicts"""

    @staticmethod
    def iterate(d, fun):  # type: (Dict, Callable[[Any, Any], None]) -> None
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
    def get_element(d, path):  # type: (Dict, Tuple) -> Any
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
    def set_element(d, path, value, default_dict=None):  # type: (Dict, Tuple, Any, Optional[Dict]) -> None
        """
        Sets element in a nested dictionary, creating additional sub-dictionaries if necessary
        :param d: Dictionary
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :param value: Value to be set
        :param default_dict: Empty dictionary to be created if missing
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
    def __init__(self, comment=''):  # type: (str) -> None
        self.comment = comment
        self._config = None

    def set_modified(self):
        """Sets the 'modified' flag in the associated config."""
        if self._config and hasattr(self._config, 'set_modified'):
            self._config.set_modified()


class ConfigValue(ConfigEntry):
    def __init__(self, comment='', default=''):  # type: (str, Any) -> None
        super().__init__(comment)
        self.default = default
        self._val = default

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, value):
        """Auto-cast config value to specified type"""
        nval = type(self.default)(value)
        if nval != self._val:
            self.set_modified()
        # TODO value verification
        self._val = nval

    def __get__(self, instance, owner):
        return self.val

    def __set__(self, instance, value):
        self.val = value

    def __repr__(self):
        return repr(self.val)

    def __str__(self):
        return str(self.val)

class Config:
    def __init__(self, config, file):  # type: (OrderedDict, str) -> None
        self._config = config
        self._modified = False

        self._file = file
        self._toml = tomlkit.document()

    def set_modified(self):
        self._modified = True

    @staticmethod
    def _set_toml_entry(toml, path, entry):  # type: (TOMLDocument, Tuple, ConfigEntry) -> None
        """
        Sets config entry in a TOML document, creating additional tables if necessary
        :param toml: TOML document
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :param entry: New config entry
        :raise ValueError: if Path is empty
        """
        if len(path) == 0:
            raise ValueError('Path length cant be 0')
        elif len(path) == 1:
            if isinstance(entry, ConfigValue):
                item = tomlkit.item(entry.val)
            else:
                item = tomlkit.table()

            if entry.comment:
                item.comment(entry.comment)

            if toml.get(path[0]) is None:
                toml.add(path[0], item)
            else:
                toml[path[0]] = item
        else:
            if path[0] not in toml:
                toml.add(path[0], tomlkit.table())

            Config._set_toml_entry(toml[path[0]], path[1:], entry)

    def _load_dict(self, cfg_dict):  # type: (Dict) -> None
        """
        Imports config values from a nested dictionary
        :param cfg_dict: Dictionary
        """
        n_values = 0
        modified = False

        for path in self._config.keys():
            entry = self._config[path]
            if not isinstance(entry, ConfigValue):
                continue

            new_value = DictUtil.get_element(cfg_dict, path)

            # Import value if present in config dict
            if new_value is not None:
                entry.val = new_value
                n_values += 1
            else:
                modified = True

        # If the imported dict covered the config spec completely,
        # mark the config as non-modified. Otherwise there are default values
        # that can be written back to the imported file
        self._modified = modified

        logging.info('Cyra config loaded. %d values imported.' % n_values)

    def load_toml(self, toml_str):  # type: (str) -> None
        """
        Imports config values from a TOML string
        :param toml_str: TOML string
        """
        self._toml = tomlkit.loads(toml_str)
        self._load_dict(self._toml.value)

    def load_flat_dict(self, flat_dict):  # type: (Dict) -> None
        """
        Imports config values from a flat dictionary.
        :param flat_dict: Flat dictionary.
        Keys are either tuples or strings with dots as separators.
        """
        for path in self._config.keys():
            entry = self._config[path]
            if not isinstance(entry, ConfigValue):
                continue

            new_value = flat_dict.get(path)

            if new_value is None:
                new_value = flat_dict.get('.'.join(path))

            if new_value is not None:
                entry.val = new_value

    def export_toml(self):  # type: () -> str
        """
        Exports the configuration as a toml-formatted string.
        Styling and comments of the imported toml file are preserved
        :return: TOML string
        """

        # For all config keys, check if they are already present in the config file
        # If not, add them
        for path in self._config.keys():
            entry = self._config[path]
            target_value = DictUtil.get_element(self._toml.value, path)

            # Add value if missing
            if target_value is None or (isinstance(entry, ConfigValue) and entry.val != target_value):
                Config._set_toml_entry(self._toml, path, entry)

        return tomlkit.dumps(self._toml)

    def load_file(self, update=True):  # type: (bool) -> None
        """
        Loads the configuration from the file.
        :param update: If set to true, config values missing in the file will be added automatically
        with their default values and comments.
        """
        if os.path.isfile(self._file):
            logging.info('Cyra is reading your config from %s' % self._file)

            with open(self._file, 'r') as f:
                toml_str = f.read()
                self.load_toml(toml_str)
        else:
            self.set_modified()

        # Write file if non existant or modified
        if update:
            self.save_file()

    def save_file(self, force=False):  # type: (bool) -> bool
        """
        If modified, saves the configuration to disk.
        :param force: Force save, even if not modified.
        :return: True if saved successfully.
        """
        if self._modified or force:
            logging.info('Cyra is writing your config to %s' % self._file)

            with open(self._file, 'w') as f:
                f.write(self.export_toml())

            self._modified = False
            return True
        return False


class ConfigBuilder:
    """Use the ConfigBuilder to specify your configuration."""
    def __init__(self):
        # Config dict: Key(tuple) -> ConfigEntry
        self._config = OrderedDict()

        # Temporary comment (will be added to next entry)
        self._tmp_comment = ''

        # Currently active path
        self._active_path = tuple()

    @staticmethod
    def _check_key(key):  # type: (str) -> None
        """
        Checks if the key has a valid format. Keys must not be empty or contain dots.
        :param key: Key
        :raise ValueError: if Key invalid
        """
        if not key:
            raise ValueError('Key must not be empty.')
        if '.' in key:
            raise ValueError('Key must not contain dots.')

    def define(self, key, default):  # type: (str, Any) -> ConfigValue
        """
        Adds a value to your config.
        :param key: Key for the new value. Must not be empty or contain dots.
        :param default: Default value. Determines the type.
        :raise ValueError: if the key collides with an existing config value/section
        :return: ConfigValue
        """
        self._check_key(key)
        npath = self._active_path + (key,)

        if npath in self._config:
            raise ValueError('Attempted to set existing entry at ' + str(npath))

        cfg_value = ConfigValue(self._tmp_comment, default)
        self._config[npath] = cfg_value
        self._tmp_comment = ''
        return cfg_value

    def comment(self, comment):  # type: (str) -> None
        """
        Adds a comment to your config. Comment will be applied to the
        value or section added next.
        :param comment: Comment string
        """
        self._tmp_comment = comment

    def push(self, key):  # type: (str) -> None
        """
        Adds a section to your config. Use ``pop()`` to exit the section.
        :param key: Key for the new section. Must not be empty or contain dots.
        :raise ValueError: if the key collides with an existing config value
        """
        self._check_key(key)
        npath = self._active_path + (key,)

        if npath in self._config:
            if isinstance(self._config[npath], ConfigValue):
                raise ValueError('Attempted to push to existing entry at ' + str(npath))
        else:
            self._config[npath] = ConfigEntry(self._tmp_comment)

        self._tmp_comment = ''
        self._active_path = npath

    def pop(self, n=1):  # type: (int) -> None
        """
        Exits a config section created by ``push()``.
        :param n: Number of sections to exit (default: 1)
        :raise ValueError: if attempted to pop
        """
        if n > len(self._active_path):
            raise ValueError('Attempted to pop %d sections when whe only had %d' % (n, len(self._active_path)))

        self._active_path = self._active_path[:-n]

    def build(self, cfg_file):  # type: (str) -> Config
        """
        Creates a new Config object.
        :param cfg_file: Config file path
        :return: Config
        """
        # Copy built config into the new Config object, but keep value references
        new_cfg_dict = copy.copy(self._config)
        new_config = Config(new_cfg_dict, cfg_file)

        # Set config reference for all entries
        for __, entry in new_cfg_dict.items():
            entry._config = new_config

        return new_config
