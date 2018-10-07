=====
kwsgi
=====

**DON'T USE IN PRODUCTION**: Yet another WSGI server implementation.

Usage
-----

Usage is like this:

.. code-block:: console

   $ kwsgi hello.py app --reload

Options are below:

.. code-block:: console

   $ kwsgi --help
   Usage: kwsgi [OPTIONS] FILEPATH WSGIAPP

     Example: kwsgi hello.py app -p 5000 --reload

   Options:
     -h, --host TEXT               The interface to bind to.
     -p, --port INTEGER            The port to bind to.
     --reload / --no-reload        Enable live reloading
     --daemonize / --no-daemonize  Detaches the server from the controlling
                                   terminal and enters the background.
     --interval INTEGER            Interval time to check file changed for
                                   reloading
     --validate / --no-validate    Validating your WSGI application complying with
                                   PEP3333 compliance.
     --help                        Show this message and exit.


And you can integrate with kwsgi from python script:

.. code-block:: python

   from kwsgi import WSGIServer


   def application(env, start_response):
       start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
       return [b'Hello World']


   if __name__ == '__main__':
       server = WSGIServer(application)
       server.run_forever()


Development Roadmap
-------------------

These are the current planned major milestones:

1. [DONE] Add minimum implementation (at least this can run django application).
2. Optimize some important performance bottlenecks using C-extensions, mypyc or Rust.
3. Add green threads implementation.
