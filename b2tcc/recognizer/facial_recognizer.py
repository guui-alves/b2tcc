import os
import cv2
from flask import current_app
import numpy

DEFAULT_MEDIA_FOLDER = current_app.config['DEFAULT_MEDIA_FOLDER']
BASE_FILES = {f: os.listdir(os.path.join(DEFAULT_MEDIA_FOLDER, f)) for f in os.listdir(DEFAULT_MEDIA_FOLDER)}


def train_recognition(folder_path):
    eigenface = cv2.face.EigenFaceRecognizer_create(num_components=10, threshold=8000)
    images = BASE_FILES.update({os.path.basename(folder_path): [os.path.join(folder_path, f) for f in os.listdir(folder_path)]})
    ids = images.keys()
    faces = list()
    for image in [j for i in images.values() for j in i]:
        faces.append(cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2GRAY))
    eigenface.train(faces, numpy.array(ids))
    user_recognition_file = os.path.join(folder_path, 'classificadoEing.yml')
    eigenface.write(user_recognition_file)
    return user_recognition_file


def user_recognized(image, recognition_file, user_id):
    faces_detector = cv2.CascadeClassifier("face_original.xml")
    recognizer = cv2.face.EigenFaceRecognizer_create()
    recognizer.read(recognition_file)
    width, height = 220, 220
    picture = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detected_faces = faces_detector.detectMultiScale(picture,
                                                     scaleFactor=1.5,
                                                     minSize=(30, 30))
    for (x, y, l, a) in detected_faces:
        face = cv2.resize(picture[y:y + a, x:x + l], (width, height))
        id, reliability = recognizer.predict(face)
        if str(id) == str(user_id):
            return True

    return False
