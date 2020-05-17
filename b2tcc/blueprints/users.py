import json
import os
import zipfile
import tempfile
import shutil
import _thread
from b2tcc.app.facial_recognition import train_recognition, user_recognized

from flask import request, Blueprint, jsonify, session, current_app
from werkzeug.utils import secure_filename

from b2tcc.db import get_table

users_blueprint = Blueprint('users', __name__)


@users_blueprint.route("/register", methods=["POST"])
def register():
    users_table = get_table('users')
    form_data = request.form.to_dict() or json.loads(request.data)
    phone_number = form_data.get('phone_number', '')
    password = form_data.get('password', '')
    if not phone_number or not password:
        return jsonify({
            'message': 'Phone number or password is missing'
        }), 400

    if next(users_table.find(phone_number=phone_number), None):
        return jsonify({
            'message': 'This number is already registered'
        }), 409

    user_id = users_table.insert(dict(phone_number=phone_number, password=password))
    session['user_id'] = user_id
    return jsonify({
        'message': 'OK'
    }), 201


@users_blueprint.route("/login", methods=["POST"])
def login():
    users_table = get_table('users')
    form_data = request.form.to_dict() or json.loads(request.data)
    phone_number = form_data.get('phone_number', '')
    password = form_data.get('password', '')
    if not phone_number or not password:
        return jsonify({
            'message': 'Phone number or password is missing'
        }), 400

    user = next(users_table.find(phone_number=phone_number), None)
    if not user:
        return jsonify({
            'message': 'This phone number is not registered'
        }), 400

    if user.get('password') == password:
        session['user_id'] = user.get('id')
        return jsonify({
            'message': 'OK'
        }), 202
    else:
        return jsonify({
            'message': 'Wrong password'
        }), 403


@users_blueprint.route("/logout", methods=["GET"])
def logout():
    session.pop('user_id', None)
    return jsonify({
        'message': 'Bye bye!'
    }), 204


@users_blueprint.route("/user", methods=["PUT", "POST"])
def user():
    users_table = get_table('users')
    id = session.get('user_id', None)
    if not id:
        return jsonify({
            'message': 'Please login'
        }), 401
    user = next(users_table.find(id=id), None)
    if not user:
        return jsonify({
            'message': 'User id not found'
        }), 400

    if request.method == "PUT":
        media_folder = os.path.join(current_app.config['MEDIA_ROOT'], str(id))
        zip = request.files.get('pictures')
        if zip:
            temp_folder = tempfile.mkdtemp()
            with zipfile.ZipFile(zip, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)
            index = 0
            for image in os.listdir(temp_folder):
                filename = secure_filename(image)
                while True:
                    path = os.path.join(media_folder, f'{index}_{filename}')
                    if os.path.exists(path):
                        index += 1
                    else:
                        break
                if not os.path.exists(media_folder):
                    os.mkdir(media_folder)
                shutil.copy2(os.path.join(temp_folder, image), path)
                pictures = user.get('pictures', None)
                data = dict(id=id, pictures=f'{pictures};{index}_{filename}' if pictures else f'{index}_{filename}')
                users_table.update(data, ['id'])
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            _thread.start_new_thread(
                users_table.update(dict(id=id, user_recognition_file=train_recognition(media_folder)), ['id']))
            return jsonify({
                'message': 'Picture saved'
            }), 200
        else:
            return jsonify({
                'message': 'No pictures received'
            }), 400
    else:
        recognition_file = user.get('user_recognition_file')
        if not recognition_file:
            return jsonify({
                'message': 'You need to train harder'
            }), 400

        image = request.files.get('image')

        if user_recognized(image,recognition_file, id):
            return jsonify({
                'message': 'OK'
            }), 202
        else:
            return jsonify({
                'message': 'Not OK'
            }), 401
