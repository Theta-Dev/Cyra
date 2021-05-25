from typing import List
import importlib

from sphinx.application import Sphinx
from sphinx.util import logging
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import StringList

import cyra

logger = logging.getLogger(__name__)


class CyradocDirective(Directive):
    required_arguments = 1
    option_spec = {
        'no-docstrings': directives.flag,
    }

    @staticmethod
    def _get_class(cfg_path, location):
        split_path = cfg_path.rsplit('.', 1)

        if len(split_path) != 2:
            logger.error('Cyradoc path must have the format <Module>.<Class>', location=location)
            return None

        modname, clsname = split_path

        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            logger.error('Cyradoc could not find module %s' % modname, location=location)
            return None

        try:
            config_cls = getattr(mod, clsname)
        except AttributeError:
            logger.error('Cyradoc could not find class %s in module %s'
                         % (clsname, modname), location=location)
            return None

        if not issubclass(config_cls, cyra.Config):
            logger.error('Class %s is not a Cyradoc class' % cfg_path, location=location)
            return None

        return config_cls

    @staticmethod
    def _new_toml_block(toml):
        literal = nodes.literal_block(toml, toml)
        literal['language'] = 'toml'
        return literal

    def run(self):  # type: () -> List[nodes.Node]
        location = self.state_machine.get_source_and_line(self.lineno)
        cfg_path = self.arguments[0]
        config_cls = self._get_class(cfg_path, location)

        if config_cls is None:
            return []

        config = config_cls('')
        result = []

        if 'no-docstrings' in self.options:
            toml = config.export_toml()
            result.append(self._new_toml_block(toml))
        else:
            for docstring, toml in config.get_docblocks():
                if docstring:
                    rst = StringList(docstring.split('\n'))
                    # Create a node.
                    node = nodes.option_string()
                    node.document = self.state.document

                    # Parse the rst.
                    self.state.nested_parse(rst, 0, node)
                    result.append(node)

                if toml:
                    result.append(self._new_toml_block(toml))

        return result


def setup(app):  # type: (Sphinx) -> None
    app.add_directive('cyradoc', CyradocDirective)
