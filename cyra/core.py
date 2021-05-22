from typing import Optional, Dict, List, Tuple, Callable, Any
from collections import OrderedDict
import os
import copy
import logging
import inspect
import tomlkit
from tomlkit.toml_document import TOMLDocument


class DictUtil:
    """A few useful functions for handling nested dicts"""

    @staticmethod
    def iterate(d, fun):  # type: (Dict, Callable[[Any, Any], None]) -> None
        """
        Iterate through a nested dictionary, calling the function ``fun`` on every key/value.

        :param d: Nested dictionary
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
        Get element from a nested dictionary

        :param d: Nested dictionary
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
    def set_element(d, path, value, default_dict=None):
        # type: (Dict, Tuple, Any, Optional[Dict]) -> None
        """
        Set element in a nested dictionary, creating additional sub-dictionaries if necessary

        :param d: Nested dictionary
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :param value: Value to be set
        :param default_dict: Empty dictionary to be created if missing
        :raise ValueError: if Path is empty
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
    """
    Base class for config entries (both value-less nodes and ConfigValues).
    Used as a data element for the config dictionary.

    The base class holds comment and docstring.
    """

    def __init__(self, comment='', docstring=''):  # type: (str, str) -> None
        """
        :param comment: Comment for cfg field
        :param docstring: Docstring for cfg field
        """
        self._comment = comment
        self._docstring = docstring


class ConfigValue(ConfigEntry):
    """
    Configuration value data element.

    Holds config value and handles validation.
    """

    def __init__(self, comment='', docstring='', default='', path=tuple(),
                 validator=None, hook=None, strict=False):
        # type: (str, str, Any, Tuple, Callable, Callable, bool) -> None
        """
        :param comment: Comment for cfg field
        :param docstring: Docstring for cfg field
        :param default: Default value for cfg field
        :param path: Cfg field path
        :param validator: Validation function/lambda. Return true if valid value.
        :param hook: Hook function. Return modified value. Raise exception if invalid value.
        :param strict: Disable auto-casting and fall back to default value if type does not match.

        :raise ValueError: if the validator/hook does not accept the default value
        """
        super().__init__(comment, docstring)
        self._default = default
        self.__val = default
        self._path = path
        self._validator = validator
        self._hook = hook
        self._strict = strict

        if not self._validate(self._default):
            raise ValueError('Validator for field [%s] does not accept default value %s'
                             % ('.'.join(self._path), repr(self._default)))

        if not self._run_hook(self._default)[0]:
            raise ValueError('Hook for field [%s] does not accept default value %s'
                             % ('.'.join(self._path), repr(self._default)))

    @property
    def _val(self):
        return self.__val

    @_val.setter
    def _val(self, value):
        """
        Auto-cast config value to specified type and validate it.

        Log error and fall back to default value if any check did not pass.
        """
        cast_val = self._cast(value)
        nval = cast_val

        if not self._validate(nval):
            self._setter_error('is invalid', cast_val)
            nval = self._default

        h_ok, nval = self._run_hook(nval)
        if not h_ok:
            self._setter_error('is invalid (hook)', cast_val)

        self.__val = nval

    def _cast(self, value):  # type: (Any) -> Any
        """
        Try to cast the input value to the type of the default value
        (unless strict mode is enabled).

        If the cast was not successful, log error and fall back to default value.

        :param value: Raw input value
        :return: Cast value / default value
        """
        if self._strict:
            if isinstance(value, type(self._default)):
                return value
            else:
                self._setter_error('is not of type (%s)' % type(self._default), value)
                return self._default
        else:
            try:
                return type(self._default)(value)
            except (TypeError, ValueError):
                self._setter_error('could not be cast to (%s)'
                                   % type(self._default).__name__, value)
                return self._default

    def _validate(self, value):  # type: (Any) -> bool
        """
        If specified, call the validator to check if the input value is valid.

        :param value: Config value to pass to the validator
        :return: is_valid
        """
        if self._validator is None:
            return True
        return self._validator(value)

    def _run_hook(self, value):  # type: (Any) -> Tuple[bool, Any]
        """
        If specified, call the hook that can apply modifications to the config value.

        :param value: Config value to pass to the hook
        :return: Tuple: hook_ok (bool), new_value
        """
        if self._hook is None:
            return True, value
        # noinspection PyBroadException
        try:
            return True, self._hook(value)
        except Exception:
            return False, self._default

    def _setter_error(self, msg, nval):  # type: (str, Any) -> None
        """Print an error message if config value could not be set."""
        logging.error('Cyra config value %s for field [%s] %s. Falling back to default value %s.'
                      % (repr(nval), '.'.join(self._path), msg, repr(self._default)))

    def __str__(self):
        return str(self._val)

    def __repr__(self):
        return repr(self._val)


class ConfigBuilder:
    """Use the ConfigBuilder to specify your configuration."""

    def __init__(self):
        # Config dict: Key(tuple) -> ConfigEntry
        self._config = OrderedDict()

        # Temporary comment (will be added to next entry)
        self._tmp_comment = ''
        self._tmp_docstring = ''

        # Currently active path
        self._active_path = tuple()

    @staticmethod
    def _check_key(key):  # type: (str) -> None
        """
        Check if the key has a valid format. Keys must not be empty or contain dots

        :param key: Key
        :raise ValueError: if Key invalid
        """
        if not key:
            raise ValueError('Key must not be empty.')
        if '.' in key:
            raise ValueError('Key must not contain dots.')

    def define(self, key, default, validator=None, hook=None, strict=False):
        # type: (str, Any, Callable, Callable, bool) -> ConfigValue
        """
        Add a value to your config.

        :param key: Key for the new value. Must not be empty or contain dots.
        :param default: Default value. Determines the type.
        :param validator: Validation function/lambda. Return true if valid value.
        :param hook: Hook function. Return modified value. Raise exception if invalid value.
        :param strict: Disable auto-casting and fall back to default value if type does not match.
        :raise ValueError: if the key collides with an existing config value/section
                           or the validator does not accept the default value
        :return: ConfigValue
        """
        self._check_key(key)
        npath = self._active_path + (key,)

        if npath in self._config:
            raise ValueError('Attempted to set existing entry at ' + str(npath))

        cfg_value = ConfigValue(self._tmp_comment, self._tmp_docstring, default, npath,
                                validator, hook, strict)
        self._config[npath] = cfg_value
        self._tmp_comment = ''
        self._tmp_docstring = ''
        return cfg_value

    def comment(self, comment):  # type: (str) -> None
        """
        Add a comment to your config. Comment will be applied to the
        value or section added next.

        :param comment: Comment string
        """
        self._tmp_comment = comment

    def docstring(self, docstring):  # type: (str) -> None
        """
        Add a docstring to your config.

        When generating your documentation using the ``.. cyradoc::`` directive,
        the config file will be split at this location and the docstring will be
        inserted.

        :param docstring: Docstring
        """
        self._tmp_docstring = inspect.cleandoc(docstring)

    def push(self, key):  # type: (str) -> None
        """
        Add a section to your config. Use ``pop()`` to exit the section.

        :param key: Key for the new section. Must not be empty or contain dots.
        :raise ValueError: if the key collides with an existing config value
        """
        self._check_key(key)
        npath = self._active_path + (key,)

        if npath in self._config:
            raise ValueError('Attempted to push to existing entry at ' + str(npath))
        else:
            self._config[npath] = ConfigEntry(self._tmp_comment, self._tmp_docstring)

        self._tmp_comment = ''
        self._tmp_docstring = ''
        self._active_path = npath

    def pop(self, n=1):  # type: (int) -> None
        """
        Exit a config section created by ``push()``.

        :param n: Number of sections to exit (default: 1)
        :raise ValueError: if attempted to pop
        """
        if n > len(self._active_path):
            raise ValueError('Attempted to pop %d sections when whe only had %d'
                             % (n, len(self._active_path)))

        self._active_path = self._active_path[:-n]

    def build(self):  # type: () -> OrderedDict
        """
        Return a copy of the built config dict

        :return: Built config
        """
        return copy.deepcopy(self._config)


# noinspection PyProtectedMember
class Config:
    """Cyra configuration class"""

    builder = ConfigBuilder()

    def __init__(self, file='config.toml', cfg_builder=None):  # type: (str, ConfigBuilder) -> None
        if cfg_builder is None:
            cfg_builder = self.builder

        # Copy builder config into the new Config object, with NEW value references
        self._config = cfg_builder.build()

        self._modified = False
        self._file = file
        self._toml = tomlkit.document()

    def __getattribute__(self, item):
        obj = object.__getattribute__(self, item)
        if isinstance(obj, ConfigValue):
            return self._config[obj._path]._val
        return obj

    def __setattr__(self, key, value):
        try:
            obj = object.__getattribute__(self, key)

            if isinstance(obj, ConfigValue):
                self._config[obj._path]._val = value
                self._modified = True
            else:
                object.__setattr__(self, key, value)
        except AttributeError:
            object.__setattr__(self, key, value)

    @staticmethod
    def _set_toml_entry(toml, path, entry):  # type: (TOMLDocument, Tuple, ConfigEntry) -> None
        """
        Set config entry in a TOML document, creating additional tables if necessary

        :param toml: TOML document
        :param path: Path tuple (for example ``('DATABASE', 'server')`` or ``('msg',)``
        :param entry: New config entry
        :raise ValueError: if Path is empty
        """
        if len(path) == 0:
            raise ValueError('Path length cant be 0')
        elif len(path) == 1:
            if isinstance(entry, ConfigValue):
                item = tomlkit.item(entry._val)
            else:
                item = tomlkit.table()

            if entry._comment:
                item.comment(entry._comment)

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
        Import config values from a nested dictionary

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
                entry._val = new_value
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
        Import config values from a TOML string

        :param toml_str: TOML string
        """
        self._toml = tomlkit.loads(toml_str)
        self._load_dict(self._toml.value)

    def load_flat_dict(self, flat_dict):  # type: (Dict) -> None
        """
        Import config values from a flat dictionary.

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
                entry._val = new_value

    @staticmethod
    def _config_to_toml(config, document):  # type: (Dict[Tuple, ConfigEntry], TOMLDocument) -> str
        """
        Write the configuration dict to a TOMLDocument and
        output a toml-formatted string.

        :param config: Config dict
        :param document: TOMLDocument
        :return: TOML string
        """
        # For all config keys, check if they are already present in the config file
        # If not, add them
        for path in config.keys():
            entry = config[path]
            target_value = DictUtil.get_element(document.value, path)

            # Add value if missing
            if target_value is None or \
               (isinstance(entry, ConfigValue) and entry._val != target_value):
                Config._set_toml_entry(document, path, entry)

        return tomlkit.dumps(document)

    def export_toml(self):  # type: () -> str
        """
        Export the configuration as a toml-formatted string.
        Styling and comments of the imported toml file are preserved

        :return: TOML string
        """
        return self._config_to_toml(self._config, self._toml)

    def load_file(self, update=True):  # type: (bool) -> None
        """
        Load the configuration from the file.

        :param update: If set to true, config values missing in the file will be added automatically
                       with their default values and comments.
        """
        if os.path.isfile(self._file):
            logging.info('Cyra is reading your config from %s' % self._file)

            with open(self._file, 'r') as f:
                toml_str = f.read()
                self.load_toml(toml_str)
        else:
            self._modified = True

        # Write file if non existent or modified
        if update:
            self.save_file()

    def save_file(self, force=False):  # type: (bool) -> bool
        """
        If modified, save the configuration to disk.

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

    def get_docblocks(self):  # type: () -> List[Tuple[str, str]]
        """
        Output the config data blockwise with the respective docstrings.

        :return: List of tuples: (Docstring, TOML string)
        """
        docstring = inspect.getdoc(self)
        result = []
        buffer = OrderedDict()

        for path, entry in self._config.items():
            if entry._docstring:
                result.append((docstring, self._config_to_toml(buffer, tomlkit.document())))

                docstring = entry._docstring
                buffer = OrderedDict()

            buffer[path] = entry

        result.append((docstring, self._config_to_toml(buffer, tomlkit.document())))
        return result
