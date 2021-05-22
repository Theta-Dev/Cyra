####
Cyra
####

Cyra is a simple config framework for Python.

Cyra's ConfigBuilder makes it easy to specify your configuration.
The config can be read from and written to a toml file.

If the config file does not exist, Cyra will generate a new one populated with initial
values and annotated with helpful comments.

For a more detailed documentation, refer to
https://cyra.rtfd.io 

Features
#######################
- Config builder
- Value fields (string, int, bool, list, dict)
- Value verification
- Infinite nesting
- Comments
- Load/generate config from file
- Write config back to file
- Sphinx Autodoc

How to use
##########

.. code-block:: python

    import cyra

    class MyConfig(cyra.Config):
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

How to access your config values:

.. code-block:: python

    >>> cfg = MyConfig('config.toml')
    >>> cfg.load_file()

    >>> cfg.msg
    'Hello World'

    >>> cfg.msg = 'Bye bye World'
    >>> cfg.save_file()
    True

Here is the resulting config file:

.. code-block:: toml

    msg = "Hello World" # Cyra says hello

    [DATABASE] # SQL Database settings
    server = "192.168.1.1" # DB server address
    port = 1443 # SQL port (default: 1443)
    username = "admin" # Credentials
    password = "my_secret_password"
    enabled = true # DB connection enabled
