import os
import cv2
from flask import current_app
import numpy


def train_recognition(pictures_folder, files_folder):
    default_media_folder = current_app.config['DEFAULT_MEDIA_FOLDER']
    images = {f: os.listdir(os.path.join(default_media_folder, f)) for f in os.listdir(default_media_folder)}
    eigenface = cv2.face.EigenFaceRecognizer_create(num_components=10, threshold=8000)
    images.update(
        {os.path.basename(pictures_folder): [os.path.join(pictures_folder, f) for f in os.listdir(pictures_folder)]})
    ids = list()
    faces = list()
    for index in images:
        for image in images[index]:
            ids.append(index)
            faces.append(cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2GRAY))
    eigenface.train(faces, numpy.array(ids))
    user_recognition_file = os.path.join(files_folder, 'EigenParameters.yml')
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
