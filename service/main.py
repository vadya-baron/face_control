import yaml
import logging
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from waitress import serve

# Components
import app.components.cropping_component as crop_com
import app.components.recognition_component as rec_com

# Controllers
import app.controllers.detect_controller as detect_con

listener_app = Flask(__name__)
listener_app.config['JSON_AS_ASCII'] = False
CORS(listener_app)
detect_controller = detect_con.DetectController()
cropping_component = crop_com.Cropping()
recognition_component = rec_com.Recognition()


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

    try:
        cropping_component.init(config['CROPPING_COMPONENT'], debug)
        recognition_component.init(config['RECOGNITION_COMPONENT'], debug)
        detect_controller.init(config)
        if not bool(config['SERVICE']['ip_cam']):
            listener(config)
        else:
            print('Прием данных с IP камеры ещё не готов')
            exit(1)
    except Exception as e:
        logging.error(e)
        print(e)
        exit(1)


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
            employee_id, messages = detect_controller.raw_direct(request, cropping_component, recognition_component)
        elif incoming_data == 2:  # Получение numpy.ndarray массива
            employee_id, messages = detect_controller.direct(request, cropping_component, recognition_component)
        elif incoming_data == 3:  # Получение Base64 строки
            employee_id, messages = detect_controller.direct_base64(request, cropping_component, recognition_component)
        else:
            employee_id = 0
            messages = ['unknown_data_format']

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['employee_id'] = employee_id

        return json_response(result)

    @listener_app.post('/recognition')
    def recognition():
        return json_response({'recognition': 'ok'})

    @listener_app.get('/statistic')
    def statistic():
        return json_response({'statistic': 'ok'})

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
