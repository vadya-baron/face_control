import logging
import numpy as np
import cv2
from app.components.cropping_component import Cropping
from app.components.recognition_component import Recognition


# print("---stream---\r\n", request.stream.read())
# print("---data---\r\n", request.data)
# print("---args---\r\n", request.args)
# print("---files---\r\n", request.files)
# print("---form---\r\n", request.form)
# print("---get_data---\r\n", request.get_data())


class DetectController:
    """
    Контроллер по поиску лица
    raw_direct:
    """

    _service: dict

    def init(self, params: dict):
        self._service = params['SERVICE']

    def raw_direct(
            self,
            request,
            cropping_component: Cropping,
            recognition_component: Recognition
    ) -> (int, list):
        try:
            data = request.files.get('file', '')
            if data.filename != '':
                image = np.asarray(bytearray(data.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                return self.__recognition(image, cropping_component, recognition_component)
            else:
                return 0, ['no_data']
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def direct(
            self,
            request,
            cropping_component: Cropping,
            recognition_component: Recognition
    ) -> (int, list):
        try:
            input_json = request.get_json(force=True)
            data = input_json['data']

            return self.__recognition(np.ndarray(data), cropping_component, recognition_component)
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def direct_base64(
            self,
            request,
            cropping_component: Cropping,
            recognition_component: Recognition
    ) -> (int, list):
        try:
            #input_json = request.get_json()
            #data_url = input_json['data']
            #img_bytes = base64.b64decode(data_url)

            #image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            return self.__recognition(np.ndarray([]), cropping_component, recognition_component)
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def __recognition(
            self,
            data: np.ndarray,
            cropping_component: Cropping,
            recognition_component: Recognition
    ) -> (int, list):
        employee_id: int = 0

        if len(data) > 0:
            crop_data, messages = cropping_component.cropping(data)

            if len(crop_data) == 0:
                return employee_id, messages + ['no_data']

            if bool(self._service['debug']):
                cv2.imwrite(self._service['debug_temp_path'] + 'result.jpg', crop_data)

            employee_id, recognition_messages = recognition_component.recognition(crop_data)

            messages += recognition_messages

            return employee_id, messages

        return employee_id, ['no_data']
