# -*- coding: UTF-8 -*-

import os
import json
from pykl import kit

app = kit.get_test_app(os.path.join(os.getcwd(), '.git'))

class Config(object):
    def __init__(self, dict_in, **kwds):
        self.__dict__.update(dict_in)
        self.__dict__.update(kwds)

    def __str__(self):
        return str(self.__dict__)

def test():
    schema = kit.models.schema
    execution = schema.execute(TEST_QUERY, context_value=Config({}))
    if execution.errors:
        raise Exception(execution.errors[0])
    data = execution.data
    outdata = json.dumps(data, indent=4, separators=(',', ': '))
    print outdata

def main():
    test()
    exit(0)

    port = int(os.environ.get("PORT", 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port, threaded=True)


TEST_QUERY = '''
{
  curRepo {
    repo_id
    repo_path
    m: master {
      ref_name
      ref_path
      commit {
        commit_id
        commit_hash
        tree {
          tree_id
          tree_path
          tree_hash
          tree_mode
          trees {
            tree_id
            tree_path
            tree_hash
            tree_mode
            trees {
              tree_id
              tree_path
              tree_hash
              tree_mode
            }
            blobs {
              blob_id
              blob_path
              blob_hash
              blob_mode
            }
          }
          blobs {
            blob_id
            blob_path
            blob_hash
            blob_mode
          }
        }
      }
    }
    master {
      ...refShow
    }
    head(name: "dev") {
      ...refShow
    }
  }
}

fragment refShow on Ref {
  ref_path
  ref_name
  commit {
    ...commitShow
  }
  commits(max_count: 3) {
    ...commitShowSelf
  }
}

fragment commitShow on Commit {
  commit_id
  commit_hash
  commit_message
  committed_date
  author {
    actor_id
    actor_name
    actor_email
  }
  committer {
    actor_id
    actor_name
    actor_email
  }
  parents {
    ...commitShowSelf
  }
}

fragment commitShowSelf on Commit {
  commit_id
  commit_hash
  commit_message
  committed_date
}
'''

if __name__ == '__main__':
    main()