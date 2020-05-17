import sys

from b2tcc.app import create_app

mode = sys.argv[1] if len(sys.argv) > 1 else 'production'
app = create_app(mode=mode)
app.run(**app.config.get_namespace('RUN_'))
