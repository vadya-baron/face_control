import logging
import datetime
import app.components.helpers.data_converter as converter

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


def _get_start_and_end_time(data: list, start: bool) -> str:
    try:
        if start:
            return data[0]['visit_date'][-8:-3]
        else:
            return data[-1]['visit_date'][-8:-3]
    except IndexError:
        return ''


def _formatting_in_date_dict(employees: list[dict]) -> dict:
    result = {}

    if len(employees) == 0:
        return result

    for item in employees:
        date = '{date:%Y-%m-%d}'.format(date=item['visit_date'])
        model = {'visit_date': '{date:%Y-%m-%d %H:%M:%S}'.format(date=item['visit_date']),
                 'employee_id': item['employee_id'], 'id': item['id'],
                 'direction': 'entered' if item['direction'] == 0 else 'came_out'}
        if result.get(date, None) is None:
            result[date] = []

        result[date].append(model)

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

    def get_employees_list(self) -> (list[dict], list):
        try:
            messages = []
            employees = self.db_repository.get_employees()
            if len(employees) == 0:
                return employees, messages

            date = '{date:%Y-%m-%d}'.format(date=datetime.datetime.now())
            statistics = self.db_repository.get_visits({
                'date_from': date + ' 00:00:00',
                'date_to': date + ' 23:59:59',
                'limit': 10000
            })
            if len(statistics) == 0:
                return employees, messages

            stat_dict = {}
            for item in statistics:
                if stat_dict.get(item['employee_id']):
                    stat_dict[item['employee_id']].append(item)
                else:
                    stat_dict[item['employee_id']] = []
                    stat_dict[item['employee_id']].append(item)

            for employee in employees:
                time_go_work = stat_dict.get(employee['id'])
                if time_go_work is None:
                    continue
                else:
                    if len(time_go_work) == 0:
                        employee['time_go_work'] = {}
                        continue

                    if len(time_go_work) == 1:
                        employee['time_go_work'] = {
                            'entered_time': _get_start_and_end_time(time_go_work, True)
                        }
                        continue

                    time_go_work = time_go_work[::len(time_go_work) - 1]

                    try:
                        if int(time_go_work[0]['direction']) == 0:
                            employee['time_go_work'] = {
                                'entered_time': _get_start_and_end_time(time_go_work, False)
                            }
                            continue
                    except IndexError:
                        employee['time_go_work'] = {
                            'entered_time': _get_start_and_end_time(time_go_work, False)
                        }
                        continue

                    employee['time_go_work'] = {
                        'entered_time': _get_start_and_end_time(time_go_work, False),
                        'came_out_time': _get_start_and_end_time(time_go_work, True)
                    }

            return employees, messages
        except Exception as e:
            logging.exception(e)
            return [], [str(e)]

    def get_statistic(self, request) -> (list[dict], list):
        filters, messages = _get_statistic_filter(request)

        employees = self.db_repository.get_employees(filters)
        if len(employees) == 0:
            return [], messages

        employees_dict = {}
        for item in employees:
            employees_dict[item['id']] = item['display_name']

        employees_visits = self.db_repository.get_visits(filters)
        if len(employees_visits) == 0:
            return [], messages

        for item in employees_visits:
            display_name = employees_dict.get(item['employee_id'])
            if display_name:
                item['display_name'] = display_name

        return employees_visits, messages

    def get_start_end_working_statistic(self, request) -> (dict, list):
        messages = []
        dataset = {}
        employees = self.db_repository.get_employees()
        if len(employees) == 0:
            return dataset, messages

        for_date = request.args.get('for_date')
        if for_date is not None:
            if date_validate(for_date):
                for_date = '{date:%Y-%m-%d}'.format(date=datetime.date.fromisoformat(for_date))
            else:
                messages.append('invalid_date_format')
                return dataset, messages
        else:
            for_date = '{date:%Y-%m-%d}'.format(date=datetime.datetime.now())

        list_start, list_end = self.db_repository.get_start_end_working(for_date)

        if len(list_start) == 0:
            return dataset, messages

        for employee in employees:
            dataset[employee['id']] = employee
            dataset[employee['id']]['stat'] = {'start_date': '', 'end_date': ''}

        for item in list_start:
            if dataset.get(item['employee_id']) is None:
                continue
            else:
                stat = {'start_date': '{date:%Y-%m-%d %H:%M}'.format(date=item['visit_date']),
                        'end_date': '',
                        'id': item['id']}

                dataset[item['employee_id']]['stat'] = stat

        if len(list_end) == 0:
            return dataset, messages

        for item in list_end:
            if dataset.get(item['employee_id']) is None:
                continue
            else:
                if dataset[item['employee_id']]['stat']['id'] != item['id']:
                    dataset[item['employee_id']]['stat']['end_date'] = '{date:%Y-%m-%d %H:%M}'.format(
                        date=item['visit_date']
                    )
                else:
                    continue

        return dataset, messages

    def get_statistic_file(self, request, in_format: str) -> (str, str, list):
        mimetypes = {
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'html': 'text/html'
        }
        in_format = in_format.lower()
        if in_format not in ['xlsx', 'csv', 'html']:
            logging.error('Формат файла не поддерживается: ' + in_format)
            return '', '', ['file_format_is_not_supported']

        employees = self.db_repository.get_employees()
        if len(employees) == 0:
            return '', mimetypes[in_format], ['employees_notfound']

        for_date = request.args.get('for_date')
        if for_date is not None:
            if date_validate(for_date):
                for_date = datetime.date.fromisoformat(for_date)
            else:
                logging.error('Не верный формат даты (for_date): ' + for_date)
                return '', mimetypes[in_format], ['invalid_date_format']

        date_from = request.args.get('date_from')
        if date_from is not None:
            if date_validate(date_from):
                date_from = datetime.date.fromisoformat(date_from)
            else:
                logging.error('Не верный формат даты (date_from): ' + date_from)
                return '', mimetypes[in_format], ['invalid_date_format']
        else:
            date_from = datetime.date.fromisoformat(datetime.date.today().strftime('%Y-%m-%d'))

        date_to = request.args.get('date_to')
        if date_to is not None:
            if date_validate(date_to):
                date_to = datetime.date.fromisoformat(date_to)
            else:
                logging.error('Не верный формат даты (date_to): ' + date_to)
                return '', mimetypes[in_format], ['invalid_date_format']
        else:
            date_to = datetime.date.fromisoformat(datetime.date.today().strftime('%Y-%m-%d'))

        delta = date_to - date_from
        delta_days = delta.days

        employee_id = request.args.get('employee_id')

        if for_date or delta_days == 0:
            if for_date is None:
                for_date = datetime.datetime.now()

            list_start, list_end = self.db_repository.get_start_end_working(
                '{date:%Y-%m-%d}'.format(date=for_date),
                employee_id
            )
            if len(list_start) == 0:
                return '', mimetypes[in_format], ['no_statistics_available']

            return self._get_file_after_conversion(
                {
                    'employees': employees,
                    'list_stat': [
                        {
                            'list_start': list_start,
                            'list_end': list_end
                        }
                    ]
                }, mimetypes[in_format], in_format
            )

        list_stat = []
        for i in range(delta_days):
            date_from += datetime.timedelta(days=i)
            list_start, list_end = self.db_repository.get_start_end_working(
                '{date:%Y-%m-%d}'.format(date=date_from),
                employee_id
            )
            if len(list_start) == 0:
                continue

            list_stat.append({'list_start': list_start, 'list_end': list_end})

        return self._get_file_after_conversion(
            {
                'employees': employees,
                'list_stat': list_stat
            }, mimetypes[in_format], in_format
        )

    def _get_file_after_conversion(self, data: dict, mimetype: str, in_format: str) -> (str, list):
        format_data = []
        list_stat = data.get('list_stat', [])

        employees_dict = {}
        dataset = {}

        for employee in data.get('employees', []):
            employees_dict[employee['id']] = employee

        if len(list_stat) == 0:
            return '', mimetype, ['no_statistics_available']

        for stat in list_stat:
            list_start = stat.get('list_start', [])
            list_end = stat.get('list_end', [])

            date_start = '{date:%Y-%m-%d}'.format(
                date=list_start[0].get('visit_date')
            )

            for start in list_start:
                employee = employees_dict.get(start['employee_id'])
                if employee is None:
                    continue
                else:
                    dataset[date_start] = {
                        'date': date_start,
                        'display_name': employee['display_name'],
                        'start_time': '{date:%H:%M}'.format(date=start['visit_date']),
                        'end_time': '--:--'
                    }

            if len(list_end) > 0:
                date_end = '{date:%Y-%m-%d}'.format(
                    date=list_end[0].get('visit_date')
                )
                for end in list_end:
                    if dataset.get(date_end) is None:
                        continue
                    else:
                        dataset[date_end]['end_time'] = '{date:%H:%M}'.format(date=end['visit_date'])

            format_data.append(dataset.get(date_start))

        if len(format_data) == 0:
            return '', mimetype, ['no_statistics_available']

        try:
            file = converter.convert(
                data=format_data,
                file_path=self._service['export_path'],
                in_format=in_format,
                index='Дата',
                header_list=['Дата', 'ФИО', 'Пришел', 'Ушел']
            )
        except Exception as e:
            logging.exception(e)
            return '', mimetype, ['can_generate_statistics', 'contact_the_technical_department']

        return file, mimetype, []
