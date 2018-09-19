# -*- coding: UTF-8 -*-

import argparse
import json
import sys
import os

import zlib

from flask import Flask, url_for

app = Flask(__name__)



def read_file(base, obj, seq="\n"):
    obj_file = os.path.join(base, obj)
    if not os.path.isfile(obj_file):
        return ''

    with open(obj_file, 'r') as rf:
        first_line = rf.readline()
        if first_line.startswith('ref: '):
            ref = first_line.split('ref: ', 1)[-1].strip()
            return read_file(base, ref)
        else:
            return seq.join([first_line] + rf.readlines()).strip()


def load_hash(base, h):
    h_file = os.path.join(base, 'objects', h[:2], h[2:])
    if not os.path.isfile(h_file):
        return ''

    with open(h_file, 'rb') as rf:
        return zlib.decompress(rf.read())


def index_view():
    head = read_file(app.git_path, 'HEAD')
    return ''.join(
        ['<h2>HEAD:</h2>', head]  +
        ['<h2>TEXT:</h2>', '<pre>' + load_hash(app.git_path, head) + '</pre>']
    )

def get_test_app(git_path):
    app.debug = True
    app.git_path = git_path

    app.add_url_rule('/', 'index', view_func=index_view,)
    return app


def main():
    parser = argparse.ArgumentParser(description='Parse and scrape any web page using GraphQL queries')

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--test', action='store_true', default=False, help='This will start a test server with a UI for querying')

    parser.add_argument('query', metavar='PAGE', nargs='?', const=1, type=str, help='The query to read')

    parser.add_argument('--output', type=argparse.FileType('w'), default=sys.stdout)

    args = parser.parse_args()

    if args.test:
        app = get_test_app()
        import webbrowser
        webbrowser.open('http://localhost:5000/')

        app.run()

if __name__ == '__main__':
    main()
