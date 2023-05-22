import logging
import numpy as np
import cv2
import os
import datetime
from app.components.repositories.db_repository_mysql import DBRepository
from app.components.cropping_component import Cropping
from app.components.recognition_component import Recognition


class EmployeesController:
    """
    Контроллер по работе с сотрудниками
    """

    _service: dict
    _recognition_component_params: dict
    _person_path: str
    _person_display_path: str
    _blocked_persons: str
    _crop_size_width: int
    _crop_size_height: int
    cropping_component: Cropping
    recognition_component: Recognition
    db_repository: DBRepository

    def init(
            self,
            params: dict,
            cropping_component: Cropping,
            recognition_component: Recognition,
            db_repository: DBRepository
    ):
        self.cropping_component = cropping_component
        self.recognition_component = recognition_component
        self._service = params['SERVICE']
        self._recognition_component_params = params['RECOGNITION_COMPONENT']
        self._person_path = params['RECOGNITION_COMPONENT']['persons_path']
        self._person_display_path = self._service['person_display_path']
        self._blocked_persons = params['RECOGNITION_COMPONENT']['blocked_persons']
        self.db_repository = db_repository

        if self._service['crop_size_width'] is None:
            self._crop_size_width = 0
        else:
            self._crop_size_width = int(self._service['crop_size_width'])

        if self._service['crop_size_height'] is None:
            self._crop_size_height = 0
        else:
            self._crop_size_height = int(self._service['crop_size_height'])

    def get_employees_list(self) -> (list[dict], list):
        try:
            messages = []
            employees = self.db_repository.get_employees()

            if len(employees) == 0:
                messages.append('employees_notfound')

            return employees, messages
        except Exception as e:
            logging.exception(e)
            return [], [str(e)]

    def add_employee(self, request) -> (dict, list):
        try:
            messages = []
            external_id = request.form.get('external_id', None)
            display_name = request.form.get('display_name', None)
            employee_position = request.form.get('employee_position', None)
            files = request.files.getlist('files[]')

            if len(files) == 0:
                messages.append('photos_not_attached')
                return {}, messages

            if display_name is None or employee_position is None:
                messages.append('not_all_required_fields_are_filled_in')
                return {}, messages

            model = {'display_name': display_name, 'employee_position': employee_position, 'external_id': external_id}

            model = self.db_repository.add_employee(model)
            employee_id = model.get('id')
            if employee_id is None:
                messages.append('employee_record_failed')
                return {}, messages

            first_image = None
            count = 1
            for file in files:
                if file.filename != '':
                    image = np.asarray(bytearray(file.read()), dtype="uint8")
                    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

                    try:
                        face_vector = self._get_crop(str(employee_id), image)
                        if len(face_vector) == 0:
                            self._remove_data(employee_id)
                            raise Exception('i_can_identify_the_face_in_the_photo')
                    except Exception as e:
                        logging.error('Error: self._get_crop')
                        logging.exception(e)
                        self._remove_data(employee_id)
                        raise Exception('i_can_identify_the_face_in_the_photo')

                    if count == 1:
                        first_image = face_vector

                    count += 1

                    face_recognize_vector, mess = self.recognition_component.get_face_encodings(face_vector)
                    if len(face_recognize_vector) == 0:
                        self._remove_data(employee_id)
                        raise Exception('i_can_identify_the_face_in_the_photo')

                    if not self.db_repository.add_vectors(int(employee_id), face_vector, face_recognize_vector):
                        self._remove_data(employee_id)
                        raise Exception('i_can_identify_the_face_in_the_photo')

            if first_image is not None:
                cv2.imwrite(self._service['person_display_path'] + str(employee_id) + '.jpg', first_image)

            return model, messages
        except Exception as e:
            logging.exception(e)
            return {}, [str(e)]

    def remove_employee(self, request) -> (list[dict], list):
        try:
            messages = []
            args = request.args
            id = args.get('id')
            if int(id) == 0:
                messages.append('i_can_delete_an_employee')
                return messages

            if not (self._remove_data(id)):
                messages.append('i_can_delete_an_employee')
                return messages

            messages.append('employee_removed')

            employees = self.db_repository.get_employees()

            if len(employees) == 0:
                messages.append('employees_notfound')

            return employees, messages
        except Exception as e:
            logging.exception(e)
            return [str(e)]

    def move_trash_employee(self, request) -> (list[dict], list):
        try:
            messages = []
            args = request.args
            id = args.get('id')
            if int(id) == 0:
                messages.append('i_can_delete_an_employee')
                return messages

            if not (self.db_repository.update_status_employee(int(id), 3)):
                messages.append('i_can_move_an_employee_to_trash')
                return messages

            messages.append('employee_has_been_moved_to_trash')

            employees = self.db_repository.get_employees()

            if len(employees) == 0:
                messages.append('employees_notfound')

            return employees, messages
        except Exception as e:
            logging.exception(e)
            return [str(e)]

    def blocked_employee(self, request) -> (list[dict], list):
        try:
            messages = []
            args = request.args
            id = args.get('id')
            if int(id) == 0:
                messages.append('i_can_delete_an_employee')
                return messages

            if not (self.db_repository.update_status_employee(int(id), 2)):
                messages.append('i_can_move_an_employee_to_trash')
                return messages

            messages.append('employee_has_been_moved_to_trash')

            employees = self.db_repository.get_employees()

            if len(employees) == 0:
                messages.append('employees_notfound')

            return employees, messages
        except Exception as e:
            logging.exception(e)
            return [str(e)]

    def _get_crop(
            self,
            employee_id: str,
            data: np.ndarray
    ) -> np.ndarray:
        if len(data) > 0:
            crop_data, messages = self.cropping_component.cropping(data)
            small = np.ndarray((0,))
            if len(crop_data) == 0:
                return np.ndarray((0,))

            if self._crop_size_width > 0 and self._crop_size_height > 0:
                small = cv2.resize(
                    crop_data,
                    (self._crop_size_width, self._crop_size_height),
                    interpolation=cv2.INTER_LINEAR
                )
            elif self._crop_size_width > 0 and self._crop_size_height == 0:
                height = crop_data.shape[0]
                width = crop_data.shape[1]
                ratio = self._crop_size_width / width
                new_height = int(height * ratio)
                small = cv2.resize(
                    crop_data,
                    (self._crop_size_width, new_height),
                    interpolation=cv2.INTER_LINEAR
                )
            else:
                small = cv2.resize(crop_data, (0, 0), fx=0.5, fy=0.5)

            cv2.imwrite(
                self._service['dataset_path'] + 'employee_id_' + employee_id + '_' +
                '{date:%Y-%m-%d_%H-%M-%S}'.format(date=datetime.datetime.now()) + '.jpg',
                small
            )

            return small

        return np.ndarray((0,))

    def _remove_data(self, employee_id: str) -> bool:
        try:
            self.db_repository.remove_employee(int(employee_id))
        except Exception as e:
            logging.exception(e)
            return False

        try:
            os.remove(self._service['person_display_path'] + str(employee_id) + '.jpg')
        except Exception as e:
            logging.exception(e)

        return True
