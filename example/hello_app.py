from kwsgi import WSGIServer


def application(env, start_response):
    start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
    return [b'Hello World']


if __name__ == '__main__':
    server = WSGIServer(application)
    server.run_forever()
