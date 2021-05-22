################
Sphinx extension
################

Document your config
####################

Having a well-documented config greatly improves the user experience of your application.
If you are documenting your Python project using Sphinx (which you should), you can
use Cyra's build-in Sphinx extension to automatically generate documentation for your config.

Configure Sphinx
================

To use the Cyradoc Sphinx extension, you have to specify it in your ``conf.py``.
Make sure Cyra as well as all dependencies required to import your config class
are installed in the Python environment from which you are running Sphinx.

.. code-block:: python

  extensions = [
      'cyra.cyradoc',
  ]


Cyradoc directive
=================

To generate documentation for your config, use the ``.. cyradoc::`` directive
with the path to the config class specified.

.. code-block:: rst

  .. cyradoc:: mymodule.config.Config

Cyradoc will insert your config as toml-formatted code blocks (see the example below).

If you have added :ref:`1_getting_started:Docstrings` to your config, Cyradoc
splits your config into multiple blocks and adds the docstrings in between.

If your config class has a docstring it will be added to the top, as well.

If you dont want to include any docstrings, use the ``:no-docstrings:`` flag.

.. code-block:: rst

  .. cyradoc:: mymodule.config.Config
    :no-docstrings:


Example
#######

.. cyradoc:: sample_cfg.Config

Source
======

.. literalinclude:: sample_cfg/__init__.py
