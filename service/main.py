import yaml
import logging
from flask import Flask, jsonify, make_response, request
from waitress import serve

# Components
import app.components.cropping_component as crop_com
import app.components.recognition_component as rec_com

# Controllers
import app.controllers.detect_controller as detect_con

listener_app = Flask(__name__)
listener_app.config['JSON_AS_ASCII'] = False

detect_controller = detect_con.DetectController()
cropping_component = crop_com.CroppingComponent()
recognition_component = rec_com.RecognitionComponent()


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

    try:
        cropping_component.init(config['CROPPING_COMPONENT'])
        recognition_component.init(config)
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
        messages[key] = translator.get(messages[key], '')

    return messages


def listener(config):
    service = config['SERVICE']
    listener_app.config['SECRET_KEY'] = service['secret_key']

    @listener_app.get('/ping')
    def ping():
        return jsonify({'ping': 'ok'})

    @listener_app.post('/detect')
    def detect():
        result = {}
        if bool(service['incoming_data_raw']):
            employee_id, messages = detect_controller.raw_direct(request, cropping_component, recognition_component)
        else:
            employee_id, messages = detect_controller.direct(request, cropping_component, recognition_component)

        result['messages'] = translate(messages, config['LANGUAGE'])
        result['employee_id'] = employee_id
        return jsonify(result)

    @listener_app.post('/recognition')
    def recognition():
        return jsonify({'recognition': 'ok'})

    @listener_app.get('/statistic')
    def statistic():
        return jsonify({'statistic': 'ok'})

    @listener_app.errorhandler(404)
    def not_found(error):
        logging.error(error)
        return make_response(jsonify({'error': 'Not found'}), 404)

    @listener_app.errorhandler(400)
    def not_found(error):
        logging.error(error)
        return make_response(jsonify({'error': 'Bad request'}), 404)

    @listener_app.errorhandler(405)
    def not_found(error):
        logging.error(error)
        return make_response(jsonify({'error': 'Method Not Allowed'}), 405)

    @listener_app.errorhandler(405)
    def not_found(error):
        logging.error(error)
        return make_response(jsonify({'error': 'Method Not Allowed'}), 405)

    serve(listener_app, host=service['host'], port=int(service['port']))


if __name__ == '__main__':
    """
    Исполняемый файл сервиса.
    """

    start_service()
