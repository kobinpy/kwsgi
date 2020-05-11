from kwsgi import serve_forever


def application(env, start_response):
    start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
    return [b'Hello World']


if __name__ == '__main__':
    serve_forever(application)
