import logging
import numpy as np
import cv2
import time
import datetime
from app.components.cropping_component import Cropping
from app.components.recognition_component import Recognition
from app.components.repositories.db_repository_mysql import DBRepository


# print("---stream---\r\n", request.stream.read())
# print("---data---\r\n", request.data)
# print("---args---\r\n", request.args)
# print("---files---\r\n", request.files)
# print("---form---\r\n", request.form)
# print("---get_data---\r\n", request.get_data())


class DetectController:
    """
    Контроллер по поиску лица
    raw_direct:
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

                employee_id, messages = self.__recognition(image)
                record_messages = self.__record_employee(employee_id)
                messages += record_messages

                return employee_id, messages
            else:
                return 0, ['no_data']
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def direct(self, request) -> (int, list):
        try:
            input_json = request.get_json(force=True)
            data = input_json['data']

            employee_id, messages = self.__recognition(np.ndarray(data))
            record_messages = self.__record_employee(employee_id)
            messages += record_messages

            return employee_id, messages
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def direct_base64(self, request) -> (int, list):
        try:
            # input_json = request.get_json()
            # data_url = input_json['data']
            # img_bytes = base64.b64decode(data_url)

            # image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            employee_id, messages = self.__recognition(np.ndarray([]))
            record_messages = self.__record_employee(employee_id)
            messages += record_messages

            return employee_id, messages
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def __recognition(
            self,
            data: np.ndarray
    ) -> (int, list):
        employee_id: int = 0

        if len(data) > 0:
            crop_data, messages = self.cropping_component.cropping(data)

            if len(crop_data) == 0:
                return employee_id, messages + ['no_data']

            if bool(self._service['debug']):
                cv2.imwrite(self._service['debug_temp_path'] + 'result.jpg', crop_data)

            employee_id, recognition_messages = self.recognition_component.recognition(crop_data)

            messages += recognition_messages

            return employee_id, messages

        return employee_id, ['no_data']

    def __record_employee(self, employee_id) -> list:
        if employee_id <= 0:
            return []

        test_time = int(time.time())
        new_employee = False

        if self.temp_dict_of_employees.get(employee_id) is None:
            self.temp_dict_of_employees[employee_id] = {'last_time_rec': test_time + self._min_time_between_rec}
            new_employee = True

        if new_employee is False and int(self.temp_dict_of_employees[employee_id]['last_time_rec']) > test_time:
            return []

        try:
            last_visit = self.db_repository.get_last_visit(employee_id, {
                'date_from': '{date:%Y-%m-%d 00:00:00}'.format(date=datetime.datetime.now())
            })

            if last_visit.get('direction', 1) == 1:
                direction = 0
            else:
                direction = 1

            self.db_repository.add_visit(employee_id, direction)
            self.temp_dict_of_employees[employee_id]['last_time_rec'] = test_time + self._min_time_between_rec
        except Exception as e:
            return [str(e)]

        return []
