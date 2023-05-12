import time
import datetime
import numpy as np
import cv2
import logging
import html.entities
from app.components.cropping_component import Cropping
from app.components.recognition_component import Recognition
from app.components.repositories.db_repository_mysql import DBRepository


def record_employee(
        temp_dict_of_employees: dict,
        min_time_between_rec: int,
        db_repository: DBRepository,
        employee_id: int
) -> list:
    """
    Вспомогательная функция контроллера для записи сотрудника в базу
        temp_dict_of_employees: временный список сотружников с последним временем прохода
        min_time_between_rec: минимальный промежуток времени для записи прохода
        db_repository: репозиторий, в который будет происходить запись прохода
        employee_id: ID сотрудника

        :return [str]
        массив с сообщениями
    """
    if employee_id <= 0:
        return []

    test_time = int(time.time())
    new_employee = False

    if temp_dict_of_employees.get(employee_id) is None:
        temp_dict_of_employees[employee_id] = {'last_time_rec': test_time + min_time_between_rec}
        new_employee = True

    if new_employee is False and int(temp_dict_of_employees[employee_id]['last_time_rec']) > test_time:
        return []

    try:
        last_visit = db_repository.get_last_visit(employee_id, {
            'date_from': '{date:%Y-%m-%d 00:00:00}'.format(date=datetime.datetime.now())
        })

        if last_visit.get('direction', 1) == 1:
            direction = 0
        else:
            direction = 1

        db_repository.add_visit(employee_id, direction)
        temp_dict_of_employees[employee_id]['last_time_rec'] = test_time + min_time_between_rec
    except Exception as e:
        return [str(e)]

    return []


def recognize(
        data: np.ndarray,
        recognition_component: Recognition,
        cropping_component: Cropping | None,
        crop: bool,
        debug: bool,
        debug_file_path: str | None
) -> (int, list):
    """
    Вспомогательная функция контроллера для распознования лица сотрудника
        data: изображение в виде массива
        recognition_component: инициализированный компонент распознования по лицу
        cropping_component: инициализированный компонент для обрезки лица
        crop: нужно ли обрезать лицо
        debug: включен ли отладочный режим
        debug_file_path: пут к файлу, куда сохранить лицо

        :return int, [str]
        ID сотрудника, массив с сообщениями
    """
    employee_id: int = 0

    if len(data) > 0:
        messages = []
        if crop and cropping_component is not None:
            crop_data, messages = cropping_component.cropping(data)

            if len(crop_data) == 0:
                return employee_id, messages + ['no_data']
        else:
            crop_data = data

        if debug and debug_file_path is not None:
            cv2.imwrite(debug_file_path, crop_data)

        employee_id, recognition_messages = recognition_component.recognition(crop_data)

        messages += recognition_messages

        return employee_id, messages

    return employee_id, ['no_data']


def date_validate(date_text: str) -> bool:
    """
    Вспомогательная функция контроллера для валидации даты
        date_text: строка даты в формате 2023-12-25 (YYYY-MM-DD)

        :return bool
    """
    try:
        datetime.date.fromisoformat(date_text)
        return True
    except Exception as e:
        logging.error(e)
        return False


def escape(text: str) -> str:
    if text is None:
        return ''

    return html.entities.codepoint2name[ord(text)]
