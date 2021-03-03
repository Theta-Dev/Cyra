from collections import OrderedDict
import copy


class Value:
    def __init__(self, default=''):
        self.default = default


class Config:
    def __init__(self, config: OrderedDict):
        self._config = config

    def iterate(self, fun):
        Config._iterate(self._config, fun)

    @staticmethod
    def _iterate(d: dict, fun):
        for key, value in d.items():
            if isinstance(value, dict):
                Config._iterate(value, fun)
            else:
                fun(key, value)

    def remove(self, fun):
        Config._remove(self._config, fun)

    @staticmethod
    def _remove(d: dict, fun):
        to_remove = []
        for key, value in d.items():
            if isinstance(value, dict):
                Config._remove(value, fun)
            elif fun(key, value):
                to_remove.append(key)

        for key in to_remove:
            d.pop(key)


class ConfigBuilder:
    def __init__(self):
        self._config = OrderedDict()

        # current_dict points to the currently active config sub-dict
        self._current_path = []
        self._current = self._config

    @staticmethod
    def _check_key(key):
        if key.startswith('_'):
            raise ValueError('Keys must not start with an underscore')

    def _update_current(self):
        self._current = self._config
        for key in self._current_path:
            self._current = self._current.setdefault(key, OrderedDict())

    def define(self, key: str, default) -> Value:
        self._check_key(key)
        value = Value(default)
        self._current[key] = value
        return value

    def comment(self, comment: str):
        cid = self._current.setdefault('__cid', 0)

        self._current['_comment' + str(cid)] = comment

        self._current['__cid'] += 1

    def push(self, key: str):
        self._check_key(key)
        self._current_path.append(key)
        self._current = self._current.setdefault(key, OrderedDict())

    def pop(self, n=1):
        if n > len(self._current_path):
            raise ValueError('Attempted to pop %d elements when whe only had %d' % (n, len(self._current_path)))

        self._current_path = self._current_path[:-n]
        self._update_current()

    def build(self) -> Config:
        # Copy built config with all its values into the new Config object
        cfg = Config(copy.deepcopy(self._config))

        # Remove all temporary values (starting with __)
        cfg.remove(lambda key, value: key.startswith('__'))
        return cfg
