import logging
import os
import datetime
from app.components.repositories.db_repository_mysql import DBRepository
from app.controllers.common_controller import date_validate, escape


def _get_statistic_filter(request) -> (dict, list):
    filters = {}
    messages = []

    id = request.args.get('id')
    employee_id = request.args.get('employee_id')
    employees_ids = request.args.getlist('employee_ids[]')
    ids = request.args.getlist('ids[]')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    direction = request.args.get('direction')
    all_data = request.args.get('all_data')
    limit = request.args.get('limit')
    page = request.args.get('page')

    # params
    if employee_id is not None:
        employee_id = int(employee_id)

    if id is not None:
        id = int(id)

    if limit is not None:
        limit = int(limit)

    if page is not None:
        page = int(page)

    if all_data is not None:
        all_data = int(all_data)

    if direction is not None:
        direction = int(direction)

    if date_from is not None:
        if date_validate(date_from):
            date_from = '{date:%Y-%m-%d 00:00:00}'.format(date=datetime.date.fromisoformat(date_from))
        else:
            messages.append('invalid_date_format')

    if date_to is not None:
        if date_validate(date_to):
            date_to = '{date:%Y-%m-%d 23:59:59}'.format(date=datetime.date.fromisoformat(date_to))
        else:
            messages.append('invalid_date_format')

    # filters
    if employee_id is not None and employee_id > 0:
        filters['employee_id'] = employee_id

    if id is not None and id > 0:
        filters['id'] = id

    if employees_ids is not None and len(employees_ids) > 0:
        employees_ids = list(map(lambda item_id: escape(item_id), employees_ids))
        filters['employee_ids'] = employees_ids

    if ids is not None and len(ids) > 0:
        ids = list(map(lambda item_id: escape(item_id), ids))
        filters['ids'] = ids

    if date_from is not None and date_from != '':
        filters['date_from'] = date_from

    if date_to is not None and date_to != '':
        filters['date_to'] = date_to

    if direction is not None:
        filters['direction'] = direction

    if all_data is not None and all_data == 1:
        return filters, messages

    if limit is not None:
        filters['limit'] = limit
    else:
        filters['limit'] = 100

    if page is not None:
        filters['page'] = page
    else:
        filters['page'] = 1

    return filters, messages


def _formatting_in_json(employees: list[dict]) -> list[dict]:
    result = []

    if len(employees) == 0:
        return result

    for item in employees:
        model = {'visit_date': '{date:%Y-%m-%d %H:%M:%S}'.format(date=item['visit_date']),
                 'employee_id': item['employee_id'], 'id': item['id'],
                 'direction': 'entered' if item['direction'] > 0 else 'came_out'}

        result.append(model)

    return result


class StatisticController:
    """
    Контроллер по получению статистики
    """

    _service: dict
    _person_path: str
    _blocked_persons: str

    db_repository: DBRepository

    def init(
            self,
            params: dict,
            db_repository: DBRepository
    ):
        self._service = params['SERVICE']
        self._person_path = params['RECOGNITION_COMPONENT']['persons_path']
        self._blocked_persons = params['RECOGNITION_COMPONENT']['blocked_persons']
        self.db_repository = db_repository

    def get_employees_list(self) -> (list, list):
        try:
            messages = []
            employees_list = []
            if self._person_path == '' and self._person_path is None:
                messages.append('person_path_notfound')
                return employees_list, messages

            employees_list = [d for d in os.listdir(path=self._person_path)
                              if os.path.isdir(os.path.join(self._person_path, d))]

            if len(employees_list) == 0:
                messages.append('person_path_notfound')
                return employees_list, messages

            if self._blocked_persons != '' and self._blocked_persons is not None:
                employees_list.remove(str(self._blocked_persons))

            return employees_list, messages
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def get_statistic(self, request, response_format: str) -> (list[dict], list):
        filters, messages = _get_statistic_filter(request)

        employees = self.db_repository.get_visits(filters)

        if len(employees) == 0:
            return employees, messages

        if response_format == 'json':
            employees = _formatting_in_json(employees)

        return employees, messages
