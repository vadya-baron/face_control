import logging
import numpy as np
from app.components.recognition_component import Recognition
from app.components.repositories.db_repository_mysql import DBRepository
from app.controllers.common_controller import record_employee, recognize


class RecognitionController:
    """
    Контроллер по распознованию лица
        init:
        recognize:
    """

    _service: dict
    _min_time_between_rec: int
    temp_dict_of_employees: dict

    recognition_component: Recognition
    db_repository: DBRepository

    def init(
            self,
            params: dict,
            temp_dict_of_employees: dict,
            recognition_component: Recognition,
            db_repository: DBRepository
    ):
        self._service = params['SERVICE']
        self.temp_dict_of_employees = temp_dict_of_employees
        self.recognition_component = recognition_component
        self.db_repository = db_repository

        if self._service['min_time_between_rec'] is None:
            self._min_time_between_rec = 60
        else:
            self._min_time_between_rec = int(self._service['min_time_between_rec'])

    def recognize(self, request) -> (int, list):
        try:
            input_json = request.get_json(force=True)
            data = input_json['data']

            employee_id, messages = recognize(
                np.ndarray(data),
                self.recognition_component,
                None,
                False,
                bool(self._service['debug']),
                self._service['debug_temp_path'] + 'recognition_controller_recognize_result.jpg'
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
            logging.error(e)
            return 0, [str(e)]
