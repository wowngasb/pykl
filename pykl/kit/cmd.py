# -*- coding: UTF-8 -*-

import argparse
import json
import sys
import os
import zlib
from pygit2 import Repository

from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy

import graphene
import graphql
from flask_graphql import GraphQLView

app = Flask(__name__)
db = SQLAlchemy(app)

import models

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


def get_test_app(git_path, config=None):
    if not os.path.isdir(git_path):
        raise ValueError('not dir:%s' % (git_path, ))

    app.config.setdefault('GIT_PATH', git_path)

    if config:
        app.config.from_object(config)

    return app

@app.route('/')
@app.route('/index')
def index():
    return GRAPHIQL_HTML

@app.route('/test')
def test():
    return 'test'

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=models.schema, graphiql=True))


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


GRAPHIQL_HTML = '''
<!DOCTYPE html>
<html>
<head>
  <style>
    html, body {
      height: 100%;
      margin: 0;
      overflow: hidden;
      width: 100%;
    }
  </style>
  <link href="http://cdn.jsdelivr.net/graphiql/0.7.1/graphiql.css" rel="stylesheet" />
  <script src="http://cdn.jsdelivr.net/fetch/0.9.0/fetch.min.js"></script>
  <script src="http://cdn.jsdelivr.net/react/15.0.0/react.min.js"></script>
  <script src="http://cdn.jsdelivr.net/react/15.0.0/react-dom.min.js"></script>
  <script src="http://cdn.jsdelivr.net/graphiql/0.7.1/graphiql.min.js"></script>
</head>
<body>
  <script>
    // Collect the URL parameters
    var parameters = {};
    window.location.search.substr(1).split('&').forEach(function (entry) {
      var eq = entry.indexOf('=');
      if (eq >= 0) {
        parameters[decodeURIComponent(entry.slice(0, eq))] =
          decodeURIComponent(entry.slice(eq + 1));
      }
    });

    // Produce a Location query string from a parameter object.
    function locationQuery(params) {
      return location.protocol + '//' + location.host + '/graphql?' + Object.keys(params).map(function (key) {
        return encodeURIComponent(key) + '=' +
          encodeURIComponent(params[key]);
      }).join('&');
    }

    // Derive a fetch URL from the current URL, sans the GraphQL parameters.
    var graphqlParamNames = {
      query: true,
      variables: true,
      operationName: true
    };

    var otherParams = {};
    for (var k in parameters) {
      if (parameters.hasOwnProperty(k) && graphqlParamNames[k] !== true) {
        otherParams[k] = parameters[k];
      }
    }
    var fetchURL = locationQuery(otherParams);

    // Defines a GraphQL fetcher using the fetch API.
    function graphQLFetcher(graphQLParams) {
      return fetch(fetchURL, {
        method: 'post',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(graphQLParams),
        credentials: 'include',
      }).then(function (response) {
        return response.text();
      }).then(function (responseBody) {
        try {
          return JSON.parse(responseBody);
        } catch (error) {
          return responseBody;
        }
      });
    }

    // When the query and variables string is edited, update the URL bar so
    // that it can be easily shared.
    function onEditQuery(newQuery) {
      parameters.query = newQuery;
      updateURL();
    }

    function onEditVariables(newVariables) {
      parameters.variables = newVariables;
      updateURL();
    }

    function onEditOperationName(newOperationName) {
      parameters.operationName = newOperationName;
      updateURL();
    }

    function updateURL() {
      history.replaceState(null, null, locationQuery(parameters));
    }

    // Render <GraphiQL /> into the body.
    ReactDOM.render(
      React.createElement(GraphiQL, {
        fetcher: graphQLFetcher,
        onEditQuery: onEditQuery,
        onEditVariables: onEditVariables,
        onEditOperationName: onEditOperationName,
        query: "",
        response: "",
        variables: null,
        operationName: null,
      }),
      document.body
    );
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
