import logging
import numpy as np
import cv2
from app.components.cropping_component import Cropping
from app.components.recognition_component import Recognition
from app.components.repositories.db_repository_mysql import DBRepository
from app.controllers.common_controller import record_employee, recognize

# print("---stream---\r\n", request.stream.read())
# print("---data---\r\n", request.data)
# print("---args---\r\n", request.args)
# print("---files---\r\n", request.files)
# print("---form---\r\n", request.form)
# print("---get_data---\r\n", request.get_data())


class DetectController:
    """
    Контроллер по поиску лица
        init:
        raw_direct:
        direct:
        direct_base64:
    """

    _service: dict
    _min_time_between_rec: int
    temp_dict_of_employees: dict

    cropping_component: Cropping
    recognition_component: Recognition
    db_repository: DBRepository

    def init(
            self,
            params: dict,
            temp_dict_of_employees: dict,
            cropping_component: Cropping,
            recognition_component: Recognition,
            db_repository: DBRepository
    ):
        self._service = params['SERVICE']
        self.temp_dict_of_employees = temp_dict_of_employees
        self.cropping_component = cropping_component
        self.recognition_component = recognition_component
        self.db_repository = db_repository

        if self._service['min_time_between_rec'] is None:
            self._min_time_between_rec = 60
        else:
            self._min_time_between_rec = int(self._service['min_time_between_rec'])

    def raw_direct(self, request) -> (int, list):
        try:
            data = request.files.get('file', '')
            if data.filename != '':
                image = np.asarray(bytearray(data.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                employee_id, messages = recognize(
                    image,
                    self.recognition_component,
                    self.cropping_component,
                    True,
                    bool(self._service['debug']),
                    self._service['debug_temp_path'] + 'detect_controller_raw_direct_result.jpg'
                )

                record_messages = record_employee(
                    self.temp_dict_of_employees,
                    self._min_time_between_rec,
                    self.db_repository,
                    employee_id
                )
                messages += record_messages

                return employee_id, messages
            else:
                return 0, ['no_data']
        except Exception as e:
            logging.exception(e)
            return 0, ['unknown_person']

    def direct(self, request) -> (int, list):
        try:
            input_json = request.get_json(force=True)
            data = input_json['data']

            employee_id, messages = recognize(
                np.ndarray(data),
                self.recognition_component,
                self.cropping_component,
                True,
                bool(self._service['debug']),
                self._service['debug_temp_path'] + 'detect_controller_direct_result.jpg'
            )

            record_messages = record_employee(
                self.temp_dict_of_employees,
                self._min_time_between_rec,
                self.db_repository,
                employee_id
            )
            messages += record_messages

            return employee_id, messages
        except Exception as e:
            logging.exception(e)
            return 0, ['unknown_person']

    def direct_base64(self, request) -> (int, list):
        try:
            # input_json = request.get_json()
            # data_url = input_json['data']
            # img_bytes = base64.b64decode(data_url)

            # image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            employee_id, messages = recognize(
                np.ndarray(np.ndarray([])),
                self.recognition_component,
                self.cropping_component,
                True,
                bool(self._service['debug']),
                self._service['debug_temp_path'] + 'detect_controller_direct_base64_result.jpg'
            )

            record_messages = record_employee(
                self.temp_dict_of_employees,
                self._min_time_between_rec,
                self.db_repository,
                employee_id
            )
            messages += record_messages

            return employee_id, messages
        except Exception as e:
            logging.exception(e)
            return 0, ['unknown_person']
