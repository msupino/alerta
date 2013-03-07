import os
import sys
import argparse
import ConfigParser

from bunch import Bunch

CONF = Bunch()  # config options can be accessed using CONF.verbose or CONF.use_syslog


def parse_args(argv, prog=None, version='unknown', cli_parser=None, daemon=True):

    if prog is None:
        prog = os.path.basename(sys.argv[0])

    OPTION_DEFAULTS = {
        'config': '/etc/alerta/alerta.conf',
        'version': 'unknown',
        'debug': False,
        'verbose': False,
        'log_dir': '/var/log/alerta',
        'log_file': '%s.log' % prog,
        'pid_dir': '/var/run/alerta',
        'use_syslog': True,
        'use_stderr': False,
        'foreground': False,
        'show_settings': False,
    }

    SYSTEM_DEFAULTS = {

        'timezone': 'Europe/London',

        'api_host': 'monitoring',
        'api_port': 80,
        'api_endpoint': '/alerta/api/v1',   # eg. /Services/API

        'server_threads': 4,
        'alert_timeout': 86400,  # seconds
        'yaml_config': '/etc/alerta/%s.yaml' % prog,
        'parser_dir': '/etc/alerta/parsers',
        'loop_every': 30,   # seconds

        'mongo_host': 'localhost',
        'mongo_port': 27017,
        'mongo_db': 'monitoring',
        'mongo_collection': 'alerts',

        'stomp_host': 'localhost',
        'stomp_port': 61613,

        'inbound_queue': '/queue/alerts',   # TODO(nsatterl): 'alert_queue' and 'alert_topic' ?
        'outbound_topic': '/topic/notify',
        'outbound_queue': '/queue/logger',

        'rabbit_host': 'localhost',
        'rabbit_port': 5672,
        'rabbit_use_ssl': False,
        'rabbit_userid': 'guest',
        'rabbit_password': 'guest',
        'rabbit_virtual_host': '/',

        'syslog_udp_port': 514,
        'syslog_tcp_port': 514,
        'syslog_facility': 'local7',

        'irc_host': 'irc.gudev.gnl',
        'irc_port': 6667,
        'irc_channel': '#alerts',
        'irc_user': 'alerta',

        'ganglia_host': 'ganglia',
        'ganglia_port': 8080,

        'es_host': 'localhost',
        'es_port': 9200,
        'es_index': 'alerta-%Y.%m.%d',  # NB. Kibana config must match this index
    }
    CONF.update(SYSTEM_DEFAULTS)

    cfg_parser = argparse.ArgumentParser(
        add_help=False
    )
    cfg_parser.add_argument(
        '-c', '--conf-file',
        help="Specify config file (default: %s)" % OPTION_DEFAULTS['config'],
        metavar="FILE",
        default=OPTION_DEFAULTS['config']
    )
    args, argv_left = cfg_parser.parse_known_args(argv)

    config_file_order = [
        args.conf_file,
        os.path.expanduser('~/.alerta.conf'),
        os.environ.get('ALERTA_CONF', ''),
    ]
    #DEBUG print 'CONFIG files => ', config_file_order

    if args.conf_file:
        config = ConfigParser.SafeConfigParser()
        config.read(config_file_order)
        defaults = config.defaults()
        if config.has_section(prog):
            for name in config.options(prog):
                if (OPTION_DEFAULTS.get(name, None) in (True, False) or
                        SYSTEM_DEFAULTS.get(name, None) in (True, False)):
                    defaults[name] = config.getboolean(prog, name)
                elif (isinstance(OPTION_DEFAULTS.get(name, None), int) or
                        isinstance(SYSTEM_DEFAULTS.get(name, None), int)):
                    defaults[name] = config.getint(prog, name)
                else:
                    defaults[name] = config.get(prog, name)
                #DEBUG print '[%s] %s = %s' % (prog, name, config.get(prog, name))
    else:
        defaults = dict()

    parents = [cfg_parser]
    if cli_parser:
        parents.append(cli_parser)

    parser = argparse.ArgumentParser(
        prog=prog,
        # description='', # TODO(nsatterl): pass __doc__ from calling program?
        parents=parents,
    )
    parser.add_argument(
        '--version',
        action='version',
        version=version
    )
    parser.add_argument(
        '--debug',
        default=OPTION_DEFAULTS['debug'],
        action='store_true',
        help="Log level DEBUG and higher (default: WARNING)"
    )
    parser.add_argument(
        '--verbose',
        default=OPTION_DEFAULTS['verbose'],
        action='store_true',
        help="Log level INFO and higher (default: WARNING)"
    )
    parser.add_argument(
        '--log-dir',
        metavar="DIR",
        default=OPTION_DEFAULTS['log_dir'],
        help="Log directory, prepended to --log-file"
    )
    parser.add_argument(
        '--log-file',
        metavar="FILE",
        default=OPTION_DEFAULTS['log_file'],
        help="Log file name"
    )
    parser.add_argument(
        '--pid-dir',
        metavar="DIR",
        default=OPTION_DEFAULTS['pid_dir'],
        help="PID directory"
    )
    parser.add_argument(
        '--use-syslog',
        default=OPTION_DEFAULTS['use_syslog'],
        action='store_true',
        help="Send errors to syslog"
    )
    parser.add_argument(
        '--use-stderr',
        default=OPTION_DEFAULTS['use_stderr'],
        action='store_true',
        help="Send to console stderr"
    )
    parser.add_argument(
        '--show-settings',
        default=OPTION_DEFAULTS['show_settings'],
        action='store_true',
        help="Output evaluated configuration options"
    )

    if daemon:
        parser.add_argument(
            '--foreground',
            default=OPTION_DEFAULTS['foreground'],
            action='store_true',
            help="Run in foreground"
        )
    parser.set_defaults(**defaults)

    args = parser.parse_args(argv_left)
    CONF.update(vars(args))

    if CONF.show_settings:
        print '[DEFAULT]'
        for k, v in sorted(CONF.iteritems()):
            print '%s = %s' % (k, v)
        sys.exit(0)