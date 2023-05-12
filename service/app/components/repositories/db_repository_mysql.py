import datetime
import logging
from typing import Tuple, Any

import pymysql.converters

from app.components.common.abstract_db_repository import Interface
from pymysql.connections import Connection as sqlConn


def _get_query(filters: dict) -> (str, str):
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
        query = query + " AND id = " + str(id)

    if employee_id:
        query = query + " AND employee_id = " + str(employee_id)

    if direction:
        query = query + " AND direction = " + str(direction)

    if date_from:
        query = query + " AND visit_date >= " + pymysql.converters.escape_str(date_from)

    if date_to:
        query = query + " AND visit_date <= " + pymysql.converters.escape_str(date_to)

    if employee_ids:
        for key, value in enumerate(employee_ids):
            employee_ids[key] = int(value)

        join_employee_ids = ','.join(employee_ids)
        query = query + " AND employee_id IN (" + join_employee_ids + ")"

    if ids:
        for key, value in enumerate(ids):
            ids[key] = int(value)

        join_ids = ','.join(ids)
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

    def add_visit(self, employee_id: int, direction: int) -> int:
        if employee_id <= 0:
            return 0
        try:
            cur = self.conn.cursor()
            visit_date = '{date:%Y-%m-%d %H:%M:%S}'.format(date=datetime.datetime.now())
            sql = "INSERT INTO `employee_visits` (`employee_id`, `visit_date`, `direction`) VALUES (%s, %s, %s)"
            cur.execute(sql, (employee_id, visit_date, direction))
            self.conn.commit()
            result = cur.lastrowid

        except Exception as e:
            logging.error(e)
            return 0

        return result

    def get_last_visit(self, employee_id: int, filters: dict) -> dict:
        query, _ = _get_query(filters)

        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM `employee_visits` WHERE employee_id=%s " + query + " ORDER BY `visit_date` DESC",
                employee_id
            )

            result = dict(cur.fetchone())

            if result.get('id') is None:
                return {}

            result['visit_date'] = result['visit_date'].strftime('%Y-%m-%d %H:%M:%S')

            return result
        except Exception as e:
            logging.error(e)

        return {}

    def get_visits(self, filters: dict) -> list[dict]:
        query, limit_offset = _get_query(filters)
        if query != '':
            query = query[4:]
            query = 'WHERE' + query

        employees = []
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM `employee_visits` " + query + " ORDER BY `visit_date` DESC" + limit_offset)
            employees = cur.fetchall()

            if len(employees) == 0:
                return []

            for row in employees:

                if not(type(row) is dict):
                    continue

                if row.get('visit_date') is datetime.datetime:
                    row['visit_date'] = row['visit_date'].strftime('%Y-%m-%d %H:%M:%S')

        except Exception as e:
            logging.error(e)

        return employees
