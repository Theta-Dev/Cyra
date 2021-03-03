from collections import OrderedDict
import copy


class DictUtil:
    @staticmethod
    def iterate(d: dict, fun):
        """
        Iterates through a nested dictionary, calling the function ``fun`` on every key/value.
        :param d:
        :param fun: Function/Lambda ``fun(key, value)``
        """
        for key, value in d.items():
            if isinstance(value, dict):
                DictUtil.iterate(value, fun)
            else:
                fun(key, value)

    @staticmethod
    def remove(d: dict, cond):
        """
        Removes all elements from nested dictionary which match the ``cond`` condition.
        :param d: Dictionary
        :param cond: Function/Lambda ``cond(key, value) -> bool``
        """
        to_remove = []
        for key, value in d.items():
            if isinstance(value, dict):
                DictUtil.remove(value, cond)
            elif cond(key, value):
                to_remove.append(key)

        for key in to_remove:
            d.pop(key)


class Value:
    def __init__(self, default=''):
        self.default = default
        self.value = default

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = value


class Config:
    def __init__(self, config: OrderedDict, comments: dict):
        self._config = config
        self._comments = comments

    def get_comment(self, path):
        return self._comments.get(tuple(path))

    def to_toml(self):
        import tomlkit

        toml = tomlkit.document()
        Config._to_toml(self, toml, self._config)
        return tomlkit.dumps(toml)

    def _to_toml(self, toml, cfg_dict: OrderedDict, path=tuple()):
        import tomlkit

        for key, value in cfg_dict.items():
            if isinstance(value, OrderedDict):
                table = tomlkit.table()
                Config._to_toml(self, table, value, path + (key,))
                toml.add(key, table)

            elif isinstance(value, Value):
                toml.add(key, value.default)
            else:
                continue

            cmt = self.get_comment(path + (key,))
            if cmt:
                toml[key].comment(cmt)

            # elif key.startswith('_comment'):
            #    toml.add(tomlkit.comment(value))


class ConfigBuilder:
    def __init__(self):
        self._config = OrderedDict()
        self._comments = dict()
        self._tmp_comment = ''

        # current_dict points to the currently active config sub-dict
        self._current_path = []
        self._current = self._config

    @staticmethod
    def _check_key(key):
        # if key.startswith('_'):
        #    raise ValueError('Keys must not start with an underscore')
        if '.' in key:
            raise ValueError('Keys must not contain dots')

    def _update_current(self):
        self._current = self._config
        for key in self._current_path:
            self._current = self._current.setdefault(key, OrderedDict())

    def define(self, key: str, default) -> Value:
        self._check_key(key)
        value = Value(default)
        self._current[key] = value
        self._add_comment(self._current_path + [key])
        return value

    def comment(self, comment: str):
        # Old method
        # cid = self._current.setdefault('__cid', 0)
        # self._current['_comment' + str(cid)] = comment
        # self._current['__cid'] += 1

        self._tmp_comment = comment

    def _add_comment(self, path):
        if self._tmp_comment:
            self._comments[tuple(path)] = self._tmp_comment
            self._tmp_comment = ''

    def push(self, key: str):
        self._check_key(key)
        self._current_path.append(key)
        self._current = self._current.setdefault(key, OrderedDict())
        self._add_comment(self._current_path)

    def pop(self, n=1):
        if n > len(self._current_path):
            raise ValueError('Attempted to pop %d elements when whe only had %d' % (n, len(self._current_path)))

        self._current_path = self._current_path[:-n]
        self._update_current()

    def build(self) -> Config:
        # Copy built config with all its values into the new Config object
        new_config = copy.deepcopy(self._config)
        new_comments = copy.deepcopy(self._comments)

        # Remove builtin values
        # DictUtil.remove(new_config, lambda key, value: key.startswith('__'))

        # Reorder, move dicts to the back
        def reorder(d: OrderedDict):
            dict_keys = []

            for key, value in d.items():
                if isinstance(value, OrderedDict):
                    reorder(value)
                    dict_keys.append(key)

            for k in dict_keys:
                d.move_to_end(k)

        reorder(new_config)

        return Config(new_config, new_comments)
