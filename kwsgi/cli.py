import os
import sys
from importlib.machinery import SourceFileLoader

import click

from .reloader import AutoReloadServer
from .server import WSGIServer
from .daemonize import daemonize as daemonize_func


def insert_import_path_to_sys_modules(import_path):
    """
    When importing a module, Python references the directories in sys.path.
    The default value of sys.path varies depending on the system, But:
    When you start Python with a script, the directory of the script is inserted into sys.path[0].
    So we have to replace sys.path to import object in specified scripts.
    """
    abspath = os.path.abspath(import_path)
    if os.path.isdir(abspath):
        sys.path.insert(0, abspath)
    else:
        sys.path.insert(0, os.path.dirname(abspath))


def run_server(app, host, port):
    click.echo('Start: {host}:{port}'.format(host=host, port=port))
    server = WSGIServer(app, host=host, port=port)
    server.run_forever()


def run_live_reloading_server(interval, app, host, port):
    click.echo('Start: {host}:{port}'.format(host=host, port=port))
    server = AutoReloadServer(run_server, kwargs={'app': app, 'host': host, 'port': port})
    server.run_forever(interval)


@click.command()
@click.argument('filepath', nargs=1, envvar='KWSGI_FILE', type=click.Path(exists=True))
@click.argument('wsgiapp', nargs=1, envvar='KWSGI_WSGI_APP')
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', envvar='KWSGI_HOST',
              help='The interface to bind to.')
@click.option('--port', '-p', type=click.INT, default=8000, envvar='KWSGI_PORT',
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=False, envvar='KWSGI_RELOAD',
              help='Enable live reloading')
@click.option('--daemonize/--no-daemonize', default=False, envvar='KWSGI_DAEMONIZE',
              help='Detaches the server from the controlling terminal and enters the background.')
@click.option('--interval', type=click.INT, default=1, envvar='KWSGI_INTERVAL',
              help='Interval time to check file changed for reloading')
@click.option('--validate/--no-validate', default=False, envvar='KWSGI_VALIDATE',
              help='Validating your WSGI application complying with PEP3333 compliance.')
def cli(filepath, wsgiapp, host, port, reload, daemonize, interval, validate):
    """
    Example: kwsgi hello.py app -p 5000 --reload
    """
    insert_import_path_to_sys_modules(filepath)
    module = SourceFileLoader('module', filepath).load_module()
    app = getattr(module, wsgiapp)

    if validate:
        from wsgiref.validate import validator
        app = validator(app)

    if reload and daemonize:
        click.echo("You couldn't use the both of --reload and --daemonize.")
        click.echo("Because when enabling daemonize option, called chdir system call"
                   " to continue to run application if the directory is removed.")
        sys.exit(1)

    if daemonize:
        daemonize_func()
        run_server(app=app, host=host, port=port)

    if reload:
        run_live_reloading_server(interval, app=app, host=host, port=port)
    else:
        run_server(app=app, host=host, port=port)
