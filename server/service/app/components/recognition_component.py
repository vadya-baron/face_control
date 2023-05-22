import fnmatch
import os
import face_recognition
import numpy as np
import logging
from app.components.common.abstract_recognition import Interface
from app.components.repositories.db_repository_mysql import DBRepository


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
    _persons = []
    _persons_display_names = {}
    _persons_vectors = []
    _known_face_encodings = {}
    _debug = False
    _tolerance = 0.5
    _blocked_persons = []
    _blocked_vectors = []
    _blocked_known_face_encodings = []
    db_repository: DBRepository

    def init(self, params: dict, db_repository: DBRepository, debug: bool):
        self._params = params
        self._debug = debug
        self._tolerance = float(params['tolerance'])
        self.db_repository = db_repository
        if self._tolerance <= 0.1:
            raise Exception('Слишком маленький допуск. Измените параметр tolerance')

        self._persons = []
        self._blocked_persons = []

        self._persons = self.db_repository.get_employees({'status': 1})
        self._blocked_persons = self.db_repository.get_employees({'status': 2})

        if len(self._persons) == 0:
            logging.info('Нет ни одного сотрудника')
            return

        persons_ids = []
        for person in self._persons:
            persons_ids.append(str(person['id']))
            self._persons_display_names[str(person['id'])] = person['display_name']

        if len(persons_ids) == 0:
            raise Exception('Нет ID сотрудников')

        self._persons_vectors = self.db_repository.get_vectors(persons_ids)

        if len(self._persons_vectors) == 0:
            raise Exception('Нет векторов для сотрудников')

        if len(self._blocked_persons) > 0:
            blocked_persons_ids = []
            for person in self._blocked_persons:
                blocked_persons_ids.append(str(person['id']))

            if len(blocked_persons_ids):
                self._blocked_vectors = self.db_repository.get_vectors(blocked_persons_ids)
                if len(self._blocked_vectors) == 0:
                    raise Exception('Нет векторов для блокированных сотрудников')

        # persons_vectors
        for vector in self._persons_vectors:
            if self._known_face_encodings.get(str(vector['employee_id'])):
                self._known_face_encodings[str(vector['employee_id'])].append(vector['face_recognize_vector'])
            else:
                self._known_face_encodings[str(vector['employee_id'])] = [vector['face_recognize_vector']]

        if len(self._known_face_encodings) == 0:
            raise Exception('Нет векторов для блокированных сотрудников')
        else:
            logging.info('Загружено персон: ' + str(len(self._known_face_encodings)))

        if len(self._blocked_vectors) > 0:
            for vector in self._blocked_vectors:
                self._blocked_known_face_encodings.append(vector['face_recognize_vector'])

    def recognition(self, image: np.ndarray) -> (int, list):
        if len(image) == 0:
            return 0, []

        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 1:
            return 0, ['only_one_face']

        encoding = encodings[0]

        # Сначала пробежим по блокированным
        if len(self._blocked_known_face_encodings) > 0:
            matches = face_recognition.compare_faces(
                self._blocked_known_face_encodings,
                encoding,
                tolerance=self._tolerance
            )
            matches_sum = sum(matches)
            if matches_sum >= 1:
                return -1, ['access_denied']

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

                return int(personId), [
                    'confirmed_person',
                    self._persons_display_names[str(personId)],
                    'recognition_success'
                ]

        return 0, ['unknown_person']

    def get_face_encodings(self, image: np.ndarray) -> (np.array, list):
        if len(image) == 0:
            return 0, []

        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 1:
            return np.array(()), ['only_one_face']

        if len(encodings) == 0:
            return np.array(()), ['i_can_identify_the_face_in_the_photo']

        return encodings[0], []
