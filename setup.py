import os
from setuptools import setup, find_packages

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(BASE_PATH, 'README.rst')).read()

__version__ = '0.0.1'
__author__ = 'Masashi Shibata'
__author_email__ = 'contact@c-bata.link'
__license__ = 'MIT License'
__classifiers__ = (
    'Development Status :: 1 - Planning',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
    'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    'Topic :: Internet :: WWW/HTTP :: WSGI',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3 :: Only',
)


setup(
    name='kwsgi',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    url='https://github.com/kobinpy/kwsgi',
    description='Yet another WSGI server implementation.',
    long_description=README,
    classifiers=__classifiers__,
    packages=find_packages(exclude=['test*']),
    install_requires=[],
    keywords='web server wsgi http',
    license=__license__,
    include_package_data=True,
    entry_points={'console_scripts': ['kwsgi = kwsgi:cli']},
    test_suite='tests',
)
