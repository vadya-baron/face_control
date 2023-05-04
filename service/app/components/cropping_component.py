import cv2
import os
import numpy as np

from app.components.common.abstract_cropping import Interface


def _is_filling(original_image=0, cropped_image=0, filling=0) -> bool:
    if original_image == 0 or cropped_image == 0 or filling == 0:
        return False

    test_filling = int((cropped_image / original_image) * 100)
    return test_filling >= filling


class Cropping(Interface):
    """
    Компонент по поиску лица, вырезание области лица и возвращение numpy.ndarray
    """

    _params = None
    _filling = None
    _face_cascade = None
    _debug = False

    def init(self, params: dict, debug: bool):
        self._params = params
        self._debug = debug

        cascade = params['cascade']
        self._filling = self._params['filling']

        if not os.path.isfile(cascade):
            raise Exception(f'Файл {cascade} не найден')

        self._face_cascade = cv2.CascadeClassifier(params['cascade'])

    def cropping(self, image: np.ndarray) -> (list, list):
        faces = self._face_cascade.detectMultiScale(image)
        cropped = []
        messages = []
        if len(faces) == 0:
            return [], []
        elif len(faces) > 1:
            messages.append('only_one_face')
        else:
            for x, y, width, height in faces:
                if self._filling:
                    original_image = image.shape[0] * image.shape[1]
                    cropped_image = (y + height) * (x + width)
                    if _is_filling(original_image, cropped_image, self._filling):
                        # bound_rect = iv2.rectangle(frame, (x, y), (x + width, y + height), color=(0, 255, 0), thickness=2)
                        cropped = image[y:y + height, x:x + width]
                    else:
                        messages.append('come_closer')

        return cropped, messages
