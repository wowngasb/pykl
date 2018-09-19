# coding: utf-8
import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

def _load_config():
    config_dir = os.path.join(basedir, 'config')
    config = os.path.join(config_dir, 'app-config.ignore.json')
    with open(config, 'r') as rf:
        output = rf.read()
        return json.loads(output) if output else {}

PHP_CONFIG = _load_config()
_ENV_DB = PHP_CONFIG.get('ENV_DB', {})

db_config = {
    'driver': _ENV_DB.get('driver', 'mysql'),
    'host': _ENV_DB.get('host', '127.0.0.1'),
    'port': _ENV_DB.get('port', 3306),
    'database': _ENV_DB.get('database', 'test') + '_tpl',
    'username': _ENV_DB.get('username', 'root'),
    'password': _ENV_DB.get('password', 'root'),
    'charset': _ENV_DB.get('charset', 'utf8'),
}


SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_DATABASE_URI = "{driver}://{username}:{password}@{host}:{port}/{database}?charset={charset}".format(**db_config)

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')