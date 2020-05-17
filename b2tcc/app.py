import os

from flask import Flask
from flask_cors import CORS

from b2tcc.blueprints.users import users_blueprint


def create_app(mode='production'):
    instance_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "%s_instance" % mode
    )
    app = Flask("B2TCC",

                instance_path=instance_path,
                instance_relative_config=True)
    CORS(app)

    app.config.from_object('b2tcc.default_settings')
    app.config.from_pyfile('config.cfg')

    app.config['MEDIA_ROOT'] = os.path.join(
        app.instance_path,
        app.config.get('MEDIA_FOLDER')
    )
    if not os.path.exists(app.config['MEDIA_ROOT']):
        os.mkdir(app.config['MEDIA_ROOT'])

    app.register_blueprint(users_blueprint)

    return app
