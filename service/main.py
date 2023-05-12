import yaml
import logging
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from waitress import serve
import pymysql
import pymysql.cursors

# import Components
import app.components.cropping_component as crop_com
import app.components.recognition_component as rec_com
import app.components.repositories.db_repository_mysql as db_rep

# import Controllers
import app.controllers.detect_controller as detect_con
import app.controllers.cropping_controller as crop_con
import app.controllers.recognition_controller as recog_con
import app.controllers.statistic_controller as stat_con

# listener
listener_app = Flask(__name__)
listener_app.config['JSON_AS_ASCII'] = False
CORS(listener_app)

# __init__ Controllers
detect_controller = detect_con.DetectController()
cropping_controller = crop_con.CroppingController()
recognition_controller = recog_con.RecognitionController()
statistic_controller = stat_con.StatisticController()

# __init__ Components
cropping_component = crop_com.Cropping()
recognition_component = rec_com.Recognition()

# __init__ Repositories
db_repository = db_rep.DBRepository()


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
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
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
        recognition_component.init(config['RECOGNITION_COMPONENT'], debug)

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

        if not bool(config['SERVICE']['ip_cam']):
            listener(config)
        else:
            print('Прием данных с IP камеры ещё не готов')
            exit(1)
    except Exception as e:
        logging.error(e)
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
        if messages[key] == 'no_data':
            del messages[key]
        else:
            messages[key] = translator.get(messages[key], '')

    return messages


def listener(config):
    service = config['SERVICE']
    listener_app.config['SECRET_KEY'] = service['secret_key']
    incoming_data = service['incoming_data']

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

    @listener_app.get('/statistic')
    def statistic():
        result = {}

        response_format = request.args.get('response_format', 'json')

        employees_list, messages = statistic_controller.get_statistic(request, response_format)

        if response_format != 'json':
            messages.append('response_format_is_not_supported')

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list



        return json_response(result)

    @listener_app.get('/get-employees-list')
    def get_employees_list():
        result = {}
        employees_list, messages = statistic_controller.get_employees_list()

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['list'] = employees_list

        return json_response(result)

    @listener_app.errorhandler(404)
    def not_found(error):
        logging.error(error)
        return json_response({'error': 'Not found'}, 404)

    @listener_app.errorhandler(400)
    def not_found(error):
        logging.error(error)
        return json_response({'error': 'Bad request'}, 404)

    @listener_app.errorhandler(405)
    def not_found(error):
        logging.error(error)
        return json_response({'error': 'Method Not Allowed'}, 405)

    @listener_app.errorhandler(405)
    def not_found(error):
        logging.error(error)
        return json_response({'error': 'Method Not Allowed'}, 405)

    print('http://' + str(service['host']) + ':' + str(service['port']))

    serve(listener_app, host=service['host'], port=int(service['port']))


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

    start_service()
