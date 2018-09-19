# coding: utf-8
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from pykl.kit import app, db

import os.path
import sys

db.engine.execute('DROP TABLE IF EXISTS `migrate_version`')

if len(sys.argv) > 1:
    dels = [i.strip() for i in sys.argv[1:] if i.strip()]
    for t in dels:
        db.engine.execute('DROP TABLE IF EXISTS `%s`' % (t, ))

db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
