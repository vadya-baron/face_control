import fnmatch
import os
import face_recognition
import numpy as np
import logging
import cv2
from app.components.common.abstract_recognition import Interface


def _get_faces(persons_path: str) -> list:
    persons = fnmatch.filter(os.listdir(persons_path), '*.jpg')
    if len(persons) == 0:
        return []

    faces_list = []
    for path in persons:
        try:
            face = face_recognition.face_encodings(
                face_recognition.load_image_file(os.path.join(persons_path, path))
            )[0]
            faces_list.append(face)
        except IndexError as e:
            logging.warning(e)

    return faces_list


class Recognition(Interface):
    """
    Компонент по распознованию лица, возвращает ID сотрудника
    """

    _params = None
    _persons = None
    _known_face_encodings = {}
    _debug = False
    _tolerance = 0.5
    _blocked_persons = 'blocked'

    def init(self, params: dict, debug: bool):
        self._params = params
        self._debug = debug
        self._tolerance = float(params['tolerance'])
        self._blocked_persons = params['blocked_persons']
        if self._tolerance <= 0.1:
            raise Exception('Слишком маленький допуск. Измените параметр tolerance')

        if 'persons_path' in params:
            persons_path = params['persons_path']
            self._persons = [d for d in os.listdir(path=persons_path)
                             if os.path.isdir(os.path.join(persons_path, d))]
        else:
            raise Exception('Не передан параметр persons_path')

        # print(self._persons)
        if not (len(self._persons) > 0):
            raise Exception(f"Папка {persons_path} пуста")

        for personId in self._persons:
            faces = _get_faces(os.path.join(persons_path, personId))
            if len(faces) > 0:
                logging.info('Append person: ' + personId)
                self._known_face_encodings[personId] = faces
            else:
                logging.info('Not append person: ' + personId)

        if len(self._known_face_encodings) == 0:
            raise Exception('Нет персон для кодирования')
        else:
            logging.info('Загружено персон: ' + str(len(self._known_face_encodings)))

    def recognition(self, image: np.ndarray) -> (int, list):
        if len(image) == 0:
            return 0, []

        small = cv2.resize(image, (0, 0), fx=1, fy=1)
        encodings = face_recognition.face_encodings(small)
        if len(encodings) != 1:
            return 0, ['only_one_face']

        encoding = encodings[0]
        for personId, person_faces in self._known_face_encodings.items():
            matches = face_recognition.compare_faces(person_faces, encoding, tolerance=self._tolerance)

            matches_sum = sum(matches)
            if matches_sum == 0:
                continue

            if personId == self._blocked_persons and matches_sum >= 1:
                return -1, ['access_denied']

            tolerance = matches_sum / len(matches)
            if tolerance >= self._tolerance:
                if personId == self._blocked_persons:
                    return -1, ['access_denied']

                return int(personId), ['confirmed_person', 'recognition_success']

        return 0, ['unknown_person']
