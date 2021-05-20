import cyra


class Config(cyra.Config):
    """
    Here is an example config to test the Cyradoc Sphinx extension.
    """

    builder = cyra.ConfigBuilder()

    builder.docstring('Specify your welcome message here')

    builder.comment('Cyra says hello')
    msg = builder.define('msg', 'Hello World')

    builder.docstring('''
    Configure your **database** here.

    .. warning::
      Keep your credentials secret!
    ''')

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

    builder.docstring('''
    Here you can add all the servers you want to observe.
    ''')

    builder.comment('Servers to be monitored')
    builder.push('SERVERS')

    builder.push('alpha')
    builder.comment('Server IP address')
    ip_a = builder.define('ip', '10.0.0.1')
    builder.comment('Set to false to disable server access')
    en_a = builder.define('enable', True)
    builder.comment('Server priority')
    prio_a = builder.define('priority', 1)
    builder.comment('Users to be handled')
    users_a = builder.define('users', ['ThetaDev', 'Clary'])
    builder.pop()

    builder.push('beta')
    builder.comment('Server IP address')
    ip_b = builder.define('ip', '10.0.0.2')
    builder.comment('Set to false to disable server access')
    en_b = builder.define('enable', False)
    builder.comment('Server priority')
    prio_b = builder.define('priority', 2)
    builder.comment('Users to be handled')
    users_b = builder.define('users', ['ThetaDev'])
    builder.pop(2)

    builder.docstring('''
    Arbitrary dictionaries can be config options, too.
    To prevent errors in your program, using a validator is recommended
    ''')
    builder.comment('Arbitrary dictionary')

    xdict = builder.define('DICT', {
        'key1': 'V1',
        'key2': 'V2',
        'key3': 'V3',
        'keyA': {
            'keyA1': 'VA1',
            'keyA2': 'VA2',
        },
        'keyB': {
            'keyB1': 'VB1',
            'keyB2': 'VB2',
        },
    })
