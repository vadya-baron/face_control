import yaml
import logging
from flask import Flask, jsonify, make_response, request, send_file
from flask_cors import CORS
from werkzeug.serving import make_server
import pymysql
import pymysql.cursors
from threading import Thread
import os

# import Components
import app.components.cropping_component as crop_com
import app.components.recognition_component as rec_com
import app.components.repositories.db_repository_mysql as db_rep

# import Controllers
import app.controllers.detect_controller as detect_con
import app.controllers.cropping_controller as crop_con
import app.controllers.recognition_controller as recog_con
import app.controllers.statistic_controller as stat_con
import app.controllers.employees_controller as employees_con

# listener
listener_app = Flask(__name__, static_url_path='', static_folder='static_files')
listener_app.config['JSON_AS_ASCII'] = False
CORS(listener_app)

# __init__ Controllers
detect_controller = detect_con.DetectController()
cropping_controller = crop_con.CroppingController()
recognition_controller = recog_con.RecognitionController()
statistic_controller = stat_con.StatisticController()
employees_controller = employees_con.EmployeesController()

# __init__ Components
cropping_component = crop_com.Cropping()
recognition_component = rec_com.Recognition()

# __init__ Repositories
db_repository = db_rep.DBRepository()


class ServerThread(Thread):

    def __init__(self, host, port, app):
        Thread.__init__(self)
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        logging.info('starting server')
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def start_server(host, port):
    global server
    server = ServerThread(host, port, listener_app)
    server.start()
    logging.info('server started')


def stop_server():
    global server
    server.shutdown()


def start_service():
    with open('./config/config.yml') as config_file:
        config = yaml.safe_load(config_file)

    if config is None:
        print('Файл с конфигурацией не найден')
        exit(1)

    logging.basicConfig(
        level=logging.DEBUG,
        filename="./logs/stream.log",
        encoding='utf-8',
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - (%(filename)s).%(funcName)s(%(lineno)d): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    debug = bool(config['SERVICE']['debug'])
    temp_dict_of_employees = dict()

    try:
        # Configure repositories
        conn = db_connect(config['DB_CONFIG'])
        db_repository.init(conn, config['DB_CONFIG'], debug)

        # Configure components
        cropping_component.init(config['CROPPING_COMPONENT'], debug)
        recognition_component.init(config['RECOGNITION_COMPONENT'], db_repository, debug)

        # Configure controllers
        detect_controller.init(
            config,
            temp_dict_of_employees,
            cropping_component,
            recognition_component,
            db_repository
        )
        cropping_controller.init(config, cropping_component)
        recognition_controller.init(config, temp_dict_of_employees, recognition_component, db_repository)
        statistic_controller.init(config, db_repository)
        employees_controller.init(config, cropping_component, recognition_component, db_repository)

        if not bool(config['SERVICE']['ip_cam']):
            listener(config)
        else:
            print('Прием данных с IP камеры ещё не готов')
            exit(1)
    except Exception as e:
        logging.exception(e)
        print(e)
        exit(1)


def db_connect(config):
    conn = pymysql.connect(host=config['host'],
                           bind_address=config['bind_address'],
                           user=config['user'],
                           password=config['password'],
                           db=config['dbname'],
                           charset=config['charset'],
                           cursorclass=pymysql.cursors.DictCursor)

    conn.ping(reconnect=True)
    conn.select_db(config['dbname'])

    return conn


def translate(messages=None, translator=None):
    if messages is None:
        return []

    if translator is None:
        return messages

    for key in range(len(messages)):
        messages[key] = translator.get(messages[key], messages[key])

    return messages


def listener(config):
    service = config['SERVICE']
    listener_app.config['SECRET_KEY'] = service['secret_key']
    incoming_data = service['incoming_data']

    @listener_app.before_request
    def hook():
        accept = request.headers.get('Accept')
        if request.method != 'OPTIONS' and service['secret_key'] != request.headers.get('AuthKey') and not(
                'image' in accept
        ):
            return json_response({'messages': translate(['access_denied'], config['LANGUAGE'])}, 403)

    @listener_app.get('/ping')
    def ping():
        return jsonify({'ping': 'ok'})

    @listener_app.post('/detect')
    def detect():
        result = {}

        if incoming_data == 1:  # Получение файла
            employee_id, messages = detect_controller.raw_direct(request)
        elif incoming_data == 2:  # Получение numpy.ndarray массива
            employee_id, messages = detect_controller.direct(request)
        elif incoming_data == 3:  # Получение Base64 строки
            employee_id, messages = detect_controller.direct_base64(request)
        else:
            employee_id = 0
            messages = ['unknown_data_format']

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['employee_id'] = employee_id

        return json_response(result)

    @listener_app.post('/crop')
    def crop():
        result = {}
        if incoming_data == 1:  # Получение файла
            id, messages = cropping_controller.raw_crop(request)
        else:
            id = 0
            messages = ['unknown_data_format']

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['id'] = id

        return json_response(result)

    @listener_app.post('/recognition')
    def recognition():
        result = {}
        id, messages = recognition_controller.recognize(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['id'] = id

        return json_response(result)

    # --------------- statistic ---------------
    @listener_app.get('/statistic/start-end-working-statistic')
    def start_end_working_statistic():
        result = {}

        response_format = request.args.get('response_format', 'json')

        employees, messages = statistic_controller.get_start_end_working_statistic(request)

        if response_format != 'json':
            messages.append('response_format_is_not_supported')

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees

        return json_response(result)

    @listener_app.get('/statistic/get-employees-list')
    def get_employees_list():
        result = {}
        employees_list, messages = statistic_controller.get_employees_list()

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    @listener_app.get('/statistic')
    def statistic():
        result = {}

        employees, messages = statistic_controller.get_statistic(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees

        return json_response(result)

    @listener_app.get('/statistic/<in_format>')
    def statistic_file(in_format):
        result = {}
        if in_format == '':
            result['messages'] = translate(
                ['file_format_is_not_supported', 'contact_the_technical_department'], config['LANGUAGE']
            )
            return json_response(result)

        file_path, mimetype, messages = statistic_controller.get_statistic_file(request, in_format)

        if file_path == '':
            result['messages'] = translate(messages, config['LANGUAGE'])
            return json_response(result)

        file = file_path.split('/')

        response = make_response(send_file(file_path, mimetype=mimetype))
        response.headers['Content-Transfer-Encoding'] = 'binary'
        response.headers['Content-Disposition'] = 'attachment; filename="' + file[-1] + '"'
        response.headers['Content-Length'] = str(os.path.getsize(file_path))
        return response

    # --------------- employees ---------------
    @listener_app.post('/employees/add-employee')
    def add_employee():
        result = {}
        employee, messages = employees_controller.add_employee(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['employee'] = employee

        return json_response(result)

    @listener_app.post('/employees/remove-employee')
    def remove_employee():
        result = {}
        employees_list, messages = employees_controller.remove_employee(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    @listener_app.post('/employees/move-trash-employee')
    def move_trash_employee():
        result = {}
        employees_list, messages = employees_controller.move_trash_employee(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    @listener_app.post('/employees/blocked-employee')
    def blocked_employee():
        result = {}
        employees_list, messages = employees_controller.blocked_employee(request)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    @listener_app.get('/employees')
    def get_employees():
        result = {}
        employees_list, messages = employees_controller.get_employees_list()

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    # --------------- service ---------------
    @listener_app.post('/service/update-employee-data')
    def update_employee_data():
        result = {}

        def work(query):
            os.system(query)
            stop_server()

        try:
            query = 'bash ' + realpath + '/restart.sh'
            thread = Thread(target=work, kwargs={'query': query})
            thread.start()
        except Exception as e:
            logging.error('ERROR: update_employee_data thread')
            logging.exception(e)

        result['messages'] = translate(['task_has_been_put_to_work'], config['LANGUAGE'])

        return json_response(result)

    @listener_app.errorhandler(400)
    def bad_request(error):
        logging.error(error)
        return json_response({'error': 'Bad request'}, 400)

    @listener_app.errorhandler(403)
    def access_denied(error):
        logging.error(error)
        return json_response({'error': 'Access_denied'}, 403)

    @listener_app.errorhandler(404)
    def not_found(error):
        logging.error(error)
        return json_response({'error': 'Not found'}, 404)

    @listener_app.errorhandler(405)
    def method_not_allowed(error):
        logging.error(error)
        return json_response({'error': 'Method Not Allowed'}, 405)

    print('http://' + str(service['host']) + ':' + str(service['port']))


    # server = create_server(listener_app, host=service['host'], port=int(service['port']))
    # server.run()
    #listener_app.run(debug=False)
    start_server(host=service['host'], port=int(service['port']))


def json_response(data, code=200):
    resp = make_response(jsonify(data), code)
    resp.headers.add('Access-Control-Allow-Methods', '*')
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.headers.add('Access-Control-Allow-Credentials', 'true')
    resp.headers.add('Vary', 'Origin')

    return resp


if __name__ == '__main__':
    """
    Исполняемый файл сервиса.
    """
    realpath = os.path.dirname(os.path.realpath(__file__))
    start_service()
