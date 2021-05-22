###############
Getting started
###############

Create a new class to hold your configuration, which inherits from the ``cyra.Config``
base class.

After instantiating the ConfigBuilder you can use it to add a new config value.

.. code-block:: python

  import cyra

  class Config(cyra.Config):
    builder = cyra.ConfigBuilder()

    builder.comment('Cyra says hello')
    msg = builder.define('msg', 'Hello World')

Now you have a simple configuration class that can be used in your project.
Simply instantiate the class with the path of your config file and tell Cyra to load it.

.. code-block:: python

  >>> cfg = MyConfig('config.toml')
  >>> cfg.load_file()

  >>> cfg.msg
  'Hello World'

If the configuration file does not exist, Cyra will write a new configuration file
to the specified location.

.. code-block:: toml

  # Cyra says hello
  msg = "Hello World"

If the file is present but some specified config fields are missing, they will be automatically
added, all while keeping existing data and comments intact.
So there is no reason to ship a config template with your application.

If you want to disable this "write-back" behavior, use ``cfg.load_file(False)``.
You can write back all config data using ``cfg.save_file()``, too.
This can be used to update configuration values programmatically.

.. code-block:: python

  >>> cfg.msg = 'Bye bye World'
  >>> cfg.save_file()
  True


Config builder
##############


Config values
=============

Use the ``builder.define('key', 'defaultvalue')`` method to add a new config value.

.. code-block:: python

  val = builder.define(key='val', default='defaultvalue',
                       validator=lambda x: x != 'forbidden',
                       hook=hook_function,
                       strict=True)

The **default** value determines the data type of the config value.
By default, Cyra automatically casts the input from the config file to this type.

With ``strict=True`` you can disable this behavior, which results in Cyra
logging an error and falling back to the default value.

You can include a **validator** function or lambda that tests the input value.
If the validator returns *False*, Cyra will log an error and fall back to the default value.
Specifying a validator that does not accept the default value results in a ``ValueError``.

The **hook** can be seen as a more advanced validator function, which can not only reject certain
values but also modify them. Simply return the modified value in the hook function.
Raising an exception within the hook function will make Cyra treat the value as invalid.

.. code-block:: python

  def hook_function(val):
      if val == 'straw':
          return 'gold'
      elif val == 'forbidden':
          raise Exception
      return val

The hook gets called after the casting and the validator.


Comments
========

The ``builder.comment('Comment')`` method creates a new comment
that will be applied to the next config value or section.

**Example:**

.. code-block:: python

  builder.comment('My comment')
  val = builder.define('val', 'defaultvalue')

.. code-block:: toml

  # My comment
  val = "defaultvalue"


Sections
========

You can add configuration values to sections to keep your
configuration well organized.

The ``builder.push('NAME')`` method is used to enter a new section.
Config values that are subsequentially added will be put in this section.
With the ``builder.pop(n)`` method you can exit the section(s) again.

Calling the push function multiple times creates nested sections.

**Example 1:**

.. code-block:: python

  builder.push('SECTION')
  val = builder.define('val', 'defaultvalue')

  builder.pop()

.. code-block:: toml

  [SECTION]
  val = "defaultvalue"

**Example 2:**

.. code-block:: python

  builder.push('SECTION')
  val = builder.define('val', 'defaultvalue')
  builder.push('SUBSECTION')
  sub_val = builder.define('sub_val', 'defaultvalue_sub')

  builder.pop(2)

.. code-block:: toml

  [SECTION]
  val = "defaultvalue"

  [SECTION.SUBSECTION]
  sub_val = "defaultvalue_sub"


Docstrings
==========

Docstrings are used by the Cyradoc :ref:`2_sphinx:Sphinx extension`.
When generating the documentation for your config, added docstrings
split the config file into blocks with the documentation text added
in between.

You can add any Sphinx-compatible rst syntax except for headings
to your docstring.

.. code-block:: python

  builder.docstring('''
  My **rst-formatted** docstring
  ''')


..
  Just add your configuration class to your project's documentation
  and Cyradoc does the rest.

  .. code:: rst

    .. cyradoc:: sample_cfg.Config

  You can use the ``builder.docstring('''My docstring''')`` method
  to split your configuration into multiple sections with added
  documentation.

  ------

  .. cyradoc:: sample_cfg.Config

