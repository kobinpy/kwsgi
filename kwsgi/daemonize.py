import os
import sys


DEVNULL = getattr(os, 'devnull', '/dev/null')


def daemonize():
    """Detaches the server from the controlling terminal and enters the background."""
    if 'KWSGI_CHILD' in os.environ:
        return

    if os.fork():
        # Exit a parent process because setsid() will be fail
        # if you're a process group leader.
        sys.exit(0)

    # Detaches the process from the controlling terminal.
    os.setsid()

    if os.fork():
        sys.exit(0)

    # Continue to run application if directory is removed.
    os.chdir('/')

    # 0o22 means 755 (777-755)
    os.umask(0o22)

    # Remap all of stdin, stdout and stderr on to /dev/null.
    # Please caution that this way couldn't support following execution:
    #   $ kwsgi ... > output.log 2>&1
    os.closerange(0, 3)
    fd_null = os.open(DEVNULL, os.O_RDWR)
    if fd_null != 0:
        os.dup2(fd_null, 0)
    os.dup2(fd_null, 1)
    os.dup2(fd_null, 2)
