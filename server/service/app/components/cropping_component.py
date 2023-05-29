import cv2
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
    _crop_margin: float
    _crop_size_width: int
    _crop_size_height: int

    def init(self, params: dict, debug: bool):
        self._params = params
        self._debug = debug
        self._filling = self._params['filling']
        self._crop_margin = self._params['crop_margin']
        self._crop_size_width = int(self._params['crop_size_width'])
        self._crop_size_height = int(self._params['crop_size_width'])
        self._face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + params['cascade'])

    def cropping(self, image: np.ndarray) -> (list, list):
        faces = self._face_cascade.detectMultiScale(image)
        cropped = []
        messages = []
        if len(faces) == 0:
            return [], []
        elif len(faces) > 1:
            messages.append('only_one_face')
        else: # если в кадре найдено только одно лицо
            face = faces[0]
            x, y, w, h = face
            original_image = image.shape[0] * image.shape[1]
            cropped_image = h * w
            if not _is_filling(original_image, cropped_image, self._filling):
                messages.append('come_closer')
            x1 = x + w
            y1 = y + h
            x_center = x + (w // 2)
            y_center = y + (h // 2)
            min_dist_to_center = min(x_center,y_center, image.shape[1]-x_center, image.shape[0]-y_center)
            desired_radius = w//2 * self._crop_margin # желаемая дистанция от центра лица до границы кадра
            if desired_radius < min_dist_to_center:
                messages.append('too_close')
            else:
                n = min_dist_to_center # дистанция от центра лица до ближайшей границы кадра
            x = int(x_center - n)
            y = int(y_center - n)
            x1 = int(x_center + n)
            y1 = int(y_center + n)
            cropped = image[y:y1, x:x1]     
            small = cv2.resize(
                cropped, 
                (self._crop_size_width, self._crop_size_height), 
                interpolation=cv2.INTER_LINEAR
                )
        return small, messages
