import os
import cv2
import numpy

WIDTH, HEIGHT = 220, 220
FACES_DETECTOR = cv2.CascadeClassifier(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "face_original.xml"))


def train_recognition(default_media_folder, pictures_folder, files_folder):
    images = {index: os.listdir(os.path.join(default_media_folder, index)) for index in
              os.listdir(default_media_folder)}
    for index, value in images.items():
        images[index] = [os.path.join(default_media_folder, index, file) for file in value]
    images.update(
        {os.path.basename(os.path.dirname(pictures_folder)): [os.path.join(pictures_folder, f) for f in
                                                              os.listdir(pictures_folder)]})

    eigenface = cv2.face.EigenFaceRecognizer_create(num_components=10, threshold=8000)
    ids = list()
    faces = list()
    for index in images:
        for image in images[index]:
            gray_image = cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2GRAY)
            face = FACES_DETECTOR.detectMultiScale(gray_image)
            for (x, y, w, h) in face:
                ids.append(int(index))
                faces.append(cv2.resize(gray_image[y:y + h, x:x + w], (WIDTH, HEIGHT)))

    eigenface.train(faces, numpy.array(ids))
    user_recognition_file = os.path.join(files_folder, 'EigenParameters.yml')
    eigenface.write(user_recognition_file)
    return user_recognition_file


def user_recognized(image, recognition_file, user_id):
    recognizer = cv2.face.EigenFaceRecognizer_create()
    recognizer.read(recognition_file)
    picture = cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2GRAY)
    detected_faces = FACES_DETECTOR.detectMultiScale(picture,
                                                     scaleFactor=1.5,
                                                     minSize=(30, 30))
    for (x, y, l, a) in detected_faces:
        face = cv2.resize(picture[y:y + a, x:x + l], (WIDTH, HEIGHT))
        id, reliability = recognizer.predict(face)
        if str(id) == str(user_id):
            return True

    return False
