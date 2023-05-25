import datetime
import logging
import pickle
import numpy as np
import pymysql.converters

from app.components.common.abstract_db_repository import Interface
from pymysql.connections import Connection as sqlConn


def _get_statistic_query(filters: dict) -> (str, str):
    if len(filters) == 0:
        return ''

    id = filters.get('id', None)
    employee_id = filters.get('employee_id', None)
    direction = filters.get('direction', None)
    date_from = filters.get('date_from', None)
    date_to = filters.get('date_to', None)
    employee_ids = filters.get('employee_ids', None)
    ids = filters.get('ids', None)
    limit = filters.get('limit', None)
    page = filters.get('page', None)

    query = ''
    if id:
        query = " id = " + str(id)

    if employee_id:
        if query == '':
            query = " employee_id = " + str(employee_id)
        else:
            query = query + " AND employee_id = " + str(employee_id)

    if direction:
        if query == '':
            query = " direction = " + str(direction)
        else:
            query = query + " AND direction = " + str(direction)

    if date_from:
        if query == '':
            query = " visit_date >= " + pymysql.converters.escape_str(date_from)
        else:
            query = query + " AND visit_date >= " + pymysql.converters.escape_str(date_from)

    if date_to:
        if query == '':
            query = " visit_date <= " + pymysql.converters.escape_str(date_to)
        else:
            query = query + " AND visit_date <= " + pymysql.converters.escape_str(date_to)

    if employee_ids:
        for key, value in enumerate(employee_ids):
            employee_ids[key] = int(value)

        join_employee_ids = ','.join(employee_ids)
        if query == '':
            query = " employee_id IN (" + join_employee_ids + ")"
        else:
            query = query + " AND employee_id IN (" + join_employee_ids + ")"

    if ids:
        for key, value in enumerate(ids):
            ids[key] = int(value)

        join_ids = ','.join(ids)
        if query == '':
            query = " id IN (" + join_ids + ")"
        else:
            query = query + " AND id IN (" + join_ids + ")"

    limit_offset = ''
    if limit:
        limit_offset = " LIMIT " + str(limit)

    if page and limit:
        offset = (page - 1) * limit
        limit_offset = limit_offset + " OFFSET " + str(offset)

    return query, limit_offset


class DBRepository(Interface):
    """
    Класс репозитория. Для учета посещаемости сотрудников
    """

    conn: sqlConn
    params: dict
    debug: bool

    def init(self, conn: sqlConn, params: dict, debug: bool):
        self.conn = conn
        self.params = params
        self.debug = debug

    # STATISTIC
    def add_visit(self, employee_id: int, direction: int) -> int:
        if employee_id <= 0:
            return 0

        cur = self.conn.cursor()
        try:
            visit_date = '{date:%Y-%m-%d %H:%M:%S}'.format(date=datetime.datetime.now())
            sql = "INSERT INTO `employee_visits` (`employee_id`, `visit_date`, `direction`) VALUES (%s, %s, %s)"
            cur.execute(sql, (employee_id, visit_date, direction))
            self.conn.commit()
            result = cur.lastrowid
            cur.close()
        except Exception as e:
            logging.exception(e)
            cur.close()
            return 0

        return result

    def get_last_visit(self, employee_id: int, filters: dict) -> dict:
        query, _ = _get_statistic_query(filters)
        if query != '':
            query = 'AND' + query

        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM `employee_visits` WHERE employee_id = %s " + query + " ORDER BY `visit_date` DESC",
                employee_id
            )

            result = cur.fetchone()
            cur.close()
            if not (dict == type(result)):
                return {}

            if result.get('id') is None:
                return {}

            result['visit_date'] = result['visit_date'].strftime('%Y-%m-%d %H:%M:%S')

            return result
        except Exception as e:
            cur.close()
            logging.exception(e)

        return {}

    def get_visits(self, filters: dict) -> list[dict]:
        query, limit_offset = _get_statistic_query(filters)
        if query != '':
            query = 'WHERE' + query

        employees = []
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `employee_visits` " + query + " ORDER BY `visit_date` DESC" + limit_offset)
            employees = cur.fetchall()
            cur.close()
            if len(employees) == 0:
                return []

            for row in employees:

                if not (type(row) is dict):
                    continue

                row['visit_date'] = '{date:%Y-%m-%d %H:%M:%S}'.format(date=row['visit_date'])

        except Exception as e:
            cur.close()
            logging.exception(e)

        return employees

    def get_start_end_working(self, for_date: str = None, employee_id: str = None) -> (list[dict], list[dict]):
        if for_date is None:
            for_date = '{date:%Y-%m-%d}'.format(date=datetime.datetime.now())

        common_where = ''
        if employee_id is not None:
            common_where = ' AND employee_id = ' + employee_id

        date_where = 'WHERE visit_date >= \'' + for_date + ' 00:00:00\' AND visit_date <= \'' + for_date + ' 23:59:59\''

        query_start = 'SELECT DISTINCT FIRST_VALUE(`id`) OVER `win` AS `id`, FIRST_VALUE(`direction`) OVER `win` AS ' \
                      '`direction`, FIRST_VALUE(`visit_date`) OVER `win` AS `visit_date`, `employee_id` FROM ' \
                      '`employee_visits` ' + date_where + ' AND direction = 0  ' + common_where + \
                      'WINDOW `win` AS (PARTITION BY `employee_id` ORDER BY `visit_date` ASC);'

        query_end = 'SELECT DISTINCT FIRST_VALUE(`id`) OVER `win` AS `id`, FIRST_VALUE(`direction`) OVER `win` AS ' \
                    '`direction`, FIRST_VALUE(`visit_date`) OVER `win` AS `visit_date`, `employee_id` FROM ' \
                    '`employee_visits` ' + date_where + '  AND direction = 1 ' + common_where + \
                    'WINDOW `win` AS (PARTITION BY `employee_id` ORDER BY `visit_date` DESC);'

        list_start = []
        list_end = []
        cur = self.conn.cursor()
        try:
            cur.execute(query_start)
            list_start = cur.fetchall()

            cur.execute(query_end)
            list_end = cur.fetchall()
            cur.close()
            if len(list_start) != 0:
                for row in list_start:

                    if not (type(row) is dict):
                        continue

                    if row.get('visit_date') is datetime.datetime:
                        row['visit_date'] = '{date:%Y-%m-%d %H:%M:%S}'.format(date=row['visit_date'])

            if len(list_end) != 0:
                for row in list_end:

                    if not (type(row) is dict):
                        continue

                    if row.get('visit_date') is datetime.datetime:
                        row['visit_date'] = '{date:%Y-%m-%d %H:%M:%S}'.format(date=row['visit_date'])

        except Exception as e:
            cur.close()
            logging.exception(e)

        return list_start, list_end

    # EMPLOYEES
    def get_employees(self, filters: dict = None) -> list[dict]:
        employees = []

        if filters is not None:
            id = filters.get('id', None)
            ids = filters.get('ids', None)
            status = filters.get('status', 1)
            query = ''
            if ids:
                for key, value in enumerate(ids):
                    ids[key] = int(value)

                join_ids = ','.join(ids)
                if query == '':
                    query = " id IN (" + join_ids + ")"
                else:
                    query = query + " AND id IN (" + join_ids + ")"

            if id:
                if query == '':
                    query = " id = " + str(id)
                else:
                    query = query + " AND id = " + str(id)

            if status:
                if query == '':
                    query = " status = " + str(status)
                else:
                    query = query + " AND status = " + str(status)

            if query != '':
                query = "WHERE" + query
        else:
            query = "WHERE status = 1"

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `employees` " + query)
            employees = cur.fetchall()
            cur.close()
            if len(employees) == 0:
                return []

            for row in employees:

                if not (type(row) is dict):
                    continue

                if row.get('date_create') is not None:
                    row['date_create'] = '{date:%Y-%m-%d %H:%M:%S}'.format(date=row['date_create'])

                if row.get('date_update') is not None:
                    row['date_update'] = '{date:%Y-%m-%d %H:%M:%S}'.format(date=row['date_update'])

        except Exception as e:
            cur.close()
            logging.exception(e)

        return employees

    def add_employee(self, model: dict) -> dict:
        if model is None:
            return {}

        external_id = model.get('external_id')
        display_name = model.get('display_name')
        employee_position = model.get('employee_position')

        if display_name is None or employee_position is None:
            raise Exception('required_fields_not_filled')

        cur = self.conn.cursor()
        try:
            date_create = '{date:%Y-%m-%d %H:%M:%S}'.format(date=datetime.datetime.now())
            sql = "INSERT INTO `employees` " \
                  "(`external_id`, `date_create`, `display_name`, `employee_position`, `status`) " \
                  "VALUES (%s, %s, %s, %s, %s)"
            cur.execute(sql, (external_id, date_create, display_name, employee_position, '1'))
            self.conn.commit()
            id = cur.lastrowid
            cur.close()
            if id == 0:
                raise Exception('employee_record_failed')

            model['id'] = id
        except Exception as e:
            cur.close()
            logging.exception(e)

        return model

    def remove_employee(self, id: int) -> bool:
        if id is None or id == 0:
            return False

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `employees` WHERE id = " + str(id))
            result = dict(cur.fetchone())

            if result.get('id') is None:
                return False

            cur.execute("DELETE FROM `employees` WHERE id = " + str(id))
            self.conn.commit()
            cur.close()
        except Exception as e:
            cur.close()
            logging.exception(e)

        return True

    def update_status_employee(self, id: int, status: int) -> bool:
        if id is None or id == 0 or status is None or status == 0:
            return False

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `employees` WHERE id = " + str(id))
            result = dict(cur.fetchone())

            if result.get('id') is None:
                return False

            cur.execute("UPDATE `employees` SET `status` = " + str(status) + " WHERE id = " + str(id))
            self.conn.commit()
            cur.close()
        except Exception as e:
            cur.close()
            logging.exception(e)

        return True

    # VECTORS
    def add_vectors(self, id: int, face_vector: np.ndarray, face_recognize_vector: np.array) -> bool:
        if id is None or id == 0 or len(face_vector) == 0 or len(face_recognize_vector) == 0:
            return False

        db_face_vector = pickle.dumps(face_vector)
        db_face_recognize_vector = pickle.dumps(face_recognize_vector)
        cur = self.conn.cursor()
        try:
            sql = "INSERT INTO `employees_vectors` (`employee_id`, `face_vector`, `face_recognize_vector`) " \
                  "VALUES (%s, %s, %s)"
            cur.execute(sql, (str(id), db_face_vector, db_face_recognize_vector))
            self.conn.commit()

            if cur.lastrowid == 0:
                cur.close()
                return False

            cur.close()
        except Exception as e:
            cur.close()
            logging.exception(e)

        return True

    def get_vectors(self, persons_ids: list) -> list[dict]:
        if persons_ids is None or len(persons_ids) == 0:
            return []

        join_ids = ','.join(persons_ids)
        query = "WHERE employee_id IN (" + join_ids + ")"
        vectors = []

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM `employees_vectors` " + query)
            vectors = cur.fetchall()
            cur.close()
            if len(vectors) == 0:
                return []

            for row in vectors:

                if not (type(row) is dict):
                    continue

                if row.get('face_vector') is not None:
                    row['face_vector'] = pickle.loads(row['face_vector'])

                if row.get('face_recognize_vector') is not None:
                    row['face_recognize_vector'] = pickle.loads(row['face_recognize_vector'])

        except Exception as e:
            cur.close()
            logging.exception(e)

        return vectors
