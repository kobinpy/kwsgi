import os
import sys
import threading
import time
import _thread


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


class AutoReloadServer:
    def __init__(self, func, args=None, kwargs=None):
        self.func = func
        self.func_args = args
        self.func_kwargs = kwargs

    def run_forever(self, interval):
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
                self.func(*self.func_args, **self.func_kwargs)
            if bgcheck.status == 'reload':
                sys.exit(EXIT_STATUS_RELOAD)
        except KeyboardInterrupt:
            pass
        except (SystemExit, MemoryError):
            raise
        except:
            time.sleep(interval)
            sys.exit(3)
