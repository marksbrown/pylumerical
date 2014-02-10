try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Python Wrapper for Lumerical FDTD Solutions',
    'author': 'Mark S. Brown',
    'url': 'https://github.com/marksbrown/pylumerical',
    'author_email': 'contact@markbrown.io',
    'version': '0.1',
    'packages': ['pylumerical'],
    'scripts': [],
    'name': 'pylumerical'
}

setup(**config)
