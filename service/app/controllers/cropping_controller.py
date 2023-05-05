import logging
import numpy as np
import cv2
import datetime
from app.components.cropping_component import Cropping


class CroppingController:
    """
    Контроллер по обрезанию лиц
    raw_crop:
    """

    _service: dict
    _crop_size_width: int
    _crop_size_height: int

    def init(self, params: dict):
        self._service = params['SERVICE']

        if self._service['crop_size_width'] is None:
            self._crop_size_width = 0
        else:
            self._crop_size_width = int(self._service['crop_size_width'])

        if self._service['crop_size_height'] is None:
            self._crop_size_height = 0
        else:
            self._crop_size_height = int(self._service['crop_size_height'])

    def raw_crop(
            self,
            request,
            cropping_component: Cropping
    ) -> (int, list):
        try:
            data = request.files.get('file', '')
            name = request.form.get('name', '')

            if name == '':
                name = '{date:%Y-%m-%d_%H-%M-%S}'.format(date=datetime.datetime.now())

            if data.filename != '':
                image = np.asarray(bytearray(data.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                return self.__crop(name, image, cropping_component)
            else:
                return 0, ['no_data']
        except Exception as e:
            logging.error(e)
            return 0, [str(e)]

    def __crop(
            self,
            name: str,
            data: np.ndarray,
            cropping_component: Cropping
    ) -> (int, list):
        if len(data) > 0:
            crop_data, messages = cropping_component.cropping(data)
            if len(crop_data) == 0:
                return 0, messages + ['no_data']

            if self._crop_size_width > 0 and self._crop_size_height > 0:
                small = cv2.resize(
                    crop_data,
                    (self._crop_size_width, self._crop_size_height),
                    interpolation=cv2.INTER_LINEAR
                )
            elif self._crop_size_width > 0 and self._crop_size_height == 0:
                height = crop_data.shape[0]
                width = crop_data.shape[1]
                ratio = self._crop_size_width / width
                new_height = int(height * ratio)
                small = cv2.resize(
                    crop_data,
                    (self._crop_size_width, new_height),
                    interpolation=cv2.INTER_LINEAR
                )
            else:
                small = cv2.resize(crop_data, (0, 0), fx=0.5, fy=0.5)

            cv2.imwrite(self._service['dataset_path'] + name + '.jpg', small)

            return 1, messages

        return 0, ['no_data']
