import json
import os
import zipfile
import tempfile
import shutil
import distutils.dir_util as dir_util
from b2tcc.recognizer.facial_recognizer import train_recognition, face_recognizer

from flask import request, Blueprint, jsonify, session, current_app
from werkzeug.utils import secure_filename

from b2tcc.db import get_table

from cryptography.fernet import Fernet

users_blueprint = Blueprint('users', __name__)


@users_blueprint.route("/register", methods=["POST"])
def register():
    users_table = get_table('users')
    cipher = Fernet(current_app.config['SECRET_KEY'])
    form_data = request.form.to_dict() or json.loads(request.data)
    phone_number = form_data.get('phone_number', '')
    password = form_data.get('password', '')
    if not phone_number or not password:
        return jsonify({
            'message': 'Phone number or password'
        }), 400

    if next(users_table.find(phone_number=phone_number), None):
        return jsonify({
            'message': 'This number is already registered'
        }), 409
    try:
        user_id = users_table.insert(dict(phone_number=phone_number, password=password))
        return jsonify({
            'message': 'OK',
            'SessionId': cipher.encrypt(str(user_id).encode()).decode()
        }), 201
    except Exception:
        return jsonify({
            'message': 'Something wrong happened'
        }), 500


@users_blueprint.route("/login", methods=["POST"])
def login():
    users_table = get_table('users')
    cipher = Fernet(current_app.config['SECRET_KEY'])
    form_data = request.form.to_dict() or json.loads(request.data)
    phone_number = form_data.get('phone_number', None)
    password = form_data.get('password', None)
    picture = request.files.get('picture', None)
    if not phone_number:
        return jsonify({
            'message': 'Phone number is missing'
        }), 400
    user = next(users_table.find(phone_number=phone_number), None)
    if not user:
        return jsonify({
            'message': 'This phone number is not registered'
        }), 400
    if picture:
        recognition_file = user.get('user_recognition_file')
        if not recognition_file or not os.path.exists(recognition_file):
            return jsonify({
                'message': 'You need to train harder'
            }), 400

        temp_folder = tempfile.mkdtemp()
        image_path = os.path.join(temp_folder, picture.filename)
        picture.save(image_path)
        is_user_recognized = face_recognizer(image_path, recognition_file, user.get('id'))
        shutil.rmtree(temp_folder)
        if is_user_recognized:
            return jsonify({
                'message': 'OK',
                'SessionId': cipher.encrypt(str(user.get('id')).encode()).decode()
            }), 202
        else:
            return jsonify({
                'message': 'Not recognized'
            }), 403
    elif password:
        if user.get('password') == password:
            return jsonify({
                'message': 'OK',
                'SessionId': cipher.encrypt(str(user.get('id')).encode()).decode()
            }), 202
        else:
            return jsonify({
                'message': 'Wrong password'
            }), 403
    else:
        return jsonify({
            'message': 'Password or picture is missing'
        }), 400


@users_blueprint.route("/train/<user_id>", methods=["POST"])
def train(user_id):
    users_table = get_table('users')
    cipher = Fernet(current_app.config['SECRET_KEY'])
    user_id = cipher.decrypt(str(user_id).encode()).decode()

    if not next(users_table.find(id=user_id), None):
        return jsonify({
            'message': 'You are busted! asshole!'
        }), 403

    user_pictures = request.files.get('pictures', None)
    if not user_pictures:
        return jsonify({
            'message': 'No pictures received'
        }), 400

    pictures_folder = os.path.join(current_app.config['MEDIA_ROOT'], user_id, 'pictures')
    files_folder = os.path.join(current_app.config['MEDIA_ROOT'], user_id, 'files')
    dir_util.mkpath(pictures_folder)
    dir_util.mkpath(files_folder)
    temp_folder = tempfile.mkdtemp()

    with zipfile.ZipFile(user_pictures, 'r') as zip_ref:
        zip_ref.extractall(temp_folder)
    index = 0
    for image in os.listdir(temp_folder):
        filename = secure_filename(image)
        while True:
            file_path = os.path.join(pictures_folder, f'{index}_{filename}')
            if os.path.exists(file_path):
                index += 1
            else:
                break
        shutil.copy2(os.path.join(temp_folder, image), file_path)
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    try:
        train_recognition(user_id, pictures_folder, files_folder)
        users_table.update(
            dict(id=user_id,
                 user_recognition_file=os.path.join(files_folder, 'EigenParameters.yml')),
            ['id'])
        return jsonify({
            'message': 'OK'
        }), 201
    except Exception:
        return jsonify({
            'message': 'Train failed'
        }), 500
