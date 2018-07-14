from setuptools import setup, find_packages

setup(name='pykl',
      version='0.1.5',
      packages=find_packages(),
      author='pykl',
      author_email='me@wowngasb.com',
      description='kltool for python, toolset for web, http, cache, dht, xml, json and so on',
      long_description=open('README.rst').read(),
      keywords='kltool html graphql xml json',
      url='http://github.com/wowngasb/pykl',
      license='MIT',
      install_requires=[
		'graphql-core==1.1',
		'graphene==1.4',
		'flask-graphql>=1.2.0',
		'pyquery==1.2.11',
		'requests==2.9.1',
		'SQLAlchemy==1.1.15',
		'six',
		'singledispatch'
      ],
      tests_require=[
      ])
