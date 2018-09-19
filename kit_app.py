# -*- coding: UTF-8 -*-

import os
from pykl import kit

app = kit.get_test_app(git_path=os.path.join(os.getcwd(), '.git'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port, threaded=True)
