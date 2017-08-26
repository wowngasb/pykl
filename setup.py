from setuptools import setup, find_packages

setup(name='pykl',
      version='0.1.1',
      download_url='git@github.com:wowngasb/pykl.git',
      packages=find_packages(),
      author='kl tool',
      author_email='me@wowngasb.com',
      description='kltool for python, toolset for web, http, cache, dht, xml, json and so on',
      long_description=open('README.rst').read(),
      keywords='kltool html graphql xml json',
      url='http://github.com/wowngasb/pykl',
      license='MIT',
      install_requires=[
          'graphene>=1.0',
          'flask-graphql>=1.2.0',
          'pyquery>=1.2.11',
          'requests>=2.9.1'
      ],
      tests_require=[
      ])
