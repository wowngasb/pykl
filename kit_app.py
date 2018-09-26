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
    Ref = kit.models.Ref
    tmp = Ref(ref_id=0, ref_name='', ref_path='')
    tmp._ref = {}

    print tmp._ref

    schema = kit.models.schema
    execution = schema.execute(TEST_QUERY, context_value=Config({}))
    if execution.errors:
        raise Exception(execution.errors[0])
    data = execution.data
    outdata = json.dumps(data, indent=4, separators=(',', ': '))
    print outdata

def main():
    # test()
    port = int(os.environ.get("PORT", 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port, threaded=True)


TEST_QUERY = '''
{
  curRepo {
    repo_id
    repo_path
    t: master {
      commit {
        tree {
          pykl_gdom_schema_py: blobfile(path: "pykl/gdom/schema.py") {
            ...blobShow
          }
          pykl_gdom: treedir(path: "pykl/gdom") {
            ...treeShow4
          }
        }
        pykl_gdom_schema_py: blobfile(path: "pykl/gdom/schema.py") {
          ...blobShow
        }
        pykl_gdom: treedir(path: "pykl/gdom") {
          ...treeShow4
        }
      }
      pykl_gdom_schema_py: blobfile(path: "pykl/gdom/schema.py") {
        ...blobShow
      }
      pykl_gdom: treedir(path: "pykl/gdom") {
        ...treeShow4
      }
    }
    m: master {
      ref_name
      ref_path
      commit {
        commit_id
        commit_hash
        tree {
          ...treeShow1
        }
      }
    }
    master {
      ...refShow
    }
    head(name: "dev") {
      ...refShow
    }
    tags {
      ...refShow
    }
    heads {
      ...refShow
    }
  }
}

fragment blobShow on Blob {
  blob_id
  blob_path
  blob_hash
  blob_mode
  blob_size
}

fragment treeShow0 on Tree {
  tree_id
  tree_path
  tree_hash
  tree_mode
  tree_size
  blobs {
    ...blobShow
  }
}

fragment treeShow1 on Tree {
  ...treeShow0
  trees {
    ...treeShow2
  }
}

fragment treeShow2 on Tree {
  ...treeShow0
  trees {
    ...treeShow3
  }
}

fragment treeShow3 on Tree {
  ...treeShow0
  trees {
    ...treeShow4
  }
}

fragment treeShow4 on Tree {
  ...treeShow0
  trees {
    ...treeShow0
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