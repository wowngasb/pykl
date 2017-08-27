import os
from pykl import gdom

app = gdom.get_test_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port, threaded=True)
