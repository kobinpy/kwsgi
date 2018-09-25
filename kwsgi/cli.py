import os
import sys
import threading
import time
import _thread
from importlib.machinery import SourceFileLoader

import click

from .server import WSGIServer


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


# For reloading server when detected python files changes.
EXIT_STATUS_RELOAD = 3


class FileCheckerThread(threading.Thread):
    # This class is copied and pasted from following source code of Bottle.
    #   https://github.com/bottlepy/bottle/blob/master/bottle.py#L3647-L3686
    """ Interrupt main-thread as soon as a changed module file is detected,
        the lockfile gets deleted or gets too old. """

    def __init__(self, lockfile, interval):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lockfile, self.interval = lockfile, interval
        #: Is one of 'reload', 'error' or 'exit'
        self.status = None

    def run(self):
        files = dict()

        for module in list(sys.modules.values()):
            path = getattr(module, '__file__', '')
            if path[-4:] in ('.pyo', '.pyc'):
                path = path[:-1]
            if path and os.path.exists(path):
                files[path] = os.stat(path).st_mtime

        while not self.status:
            if not os.path.exists(self.lockfile) or \
                    os.stat(self.lockfile).st_mtime < time.time() - self.interval - 5:
                self.status = 'error'
                _thread.interrupt_main()
            for path, last_mtime in files.items():
                if not os.path.exists(path) or os.stat(path).st_mtime > last_mtime:
                    self.status = 'reload'
                    _thread.interrupt_main()
                    break
            time.sleep(self.interval)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, *_):
        if not self.status:
            self.status = 'exit'  # silent exit
        self.join()
        return exc_type is not None and issubclass(exc_type, KeyboardInterrupt)


def run_live_reloading_server(interval, app, host, port):
    if not os.environ.get('KWSGI_CHILD'):
        import subprocess
        import tempfile
        lockfile = None
        try:
            fd, lockfile = tempfile.mkstemp(prefix='kwsgi.', suffix='.lock')
            os.close(fd)  # We only need this file to exist. We never write to it
            while os.path.exists(lockfile):
                args = [sys.executable] + sys.argv
                environ = os.environ.copy()
                environ['KWSGI_CHILD'] = 'true'
                environ['KWSGI_LOCKFILE'] = lockfile
                p = subprocess.Popen(args, env=environ)
                while p.poll() is None:  # Busy wait...
                    os.utime(lockfile, None)  # Alive! If lockfile is unlinked, it raises FileNotFoundError.
                    time.sleep(interval)
                if p.poll() != EXIT_STATUS_RELOAD:
                    if os.path.exists(lockfile):
                        os.unlink(lockfile)
                        sys.exit(p.poll())
        except KeyboardInterrupt:
            pass
        finally:
            if os.path.exists(lockfile):
                os.unlink(lockfile)
        return

    try:
        lockfile = os.environ.get('KWSGI_LOCKFILE')
        bgcheck = FileCheckerThread(lockfile, interval)
        with bgcheck:
            run_server(app=app, host=host, port=port)
        if bgcheck.status == 'reload':
            sys.exit(EXIT_STATUS_RELOAD)
    except KeyboardInterrupt:
        pass
    except (SystemExit, MemoryError):
        raise
    except:
        time.sleep(interval)
        sys.exit(3)


@click.command()
@click.argument('filepath', nargs=1, envvar='WSGICLI_FILE', type=click.Path(exists=True))
@click.argument('wsgiapp', nargs=1, envvar='WSGICLI_WSGI_APP')
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', envvar='WSGICLI_HOST',
              help='The interface to bind to.')
@click.option('--port', '-p', type=click.INT, default=8000, envvar='WSGICLI_PORT',
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=None, envvar='WSGICLI_RELOAD',
              help='Enable live reloading')
@click.option('--interval', type=click.INT, default=1, envvar='WSGICLI_INTERVAL',
              help='Interval time to check file changed for reloading')
@click.option('--validate/--no-validate', default=False, envvar='WSGICLI_VALIDATE',
              help='Validating your WSGI application complying with PEP3333 compliance.')
def cli(filepath, wsgiapp, host, port, reload, interval, validate):
    """
    Example: kwsgi hello.py app -p 5000 --reload
    """
    insert_import_path_to_sys_modules(filepath)
    module = SourceFileLoader('module', filepath).load_module()
    app = getattr(module, wsgiapp)

    if validate:
        from wsgiref.validate import validator
        app = validator(app)

    if reload:
        run_live_reloading_server(interval, app=app, host=host, port=port)
    else:
        run_server(app=app, host=host, port=port)
