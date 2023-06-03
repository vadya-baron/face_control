import cv2
import numpy as np
from typing import Tuple
from app.components.common.abstract_cropping import Interface

class Cropping(Interface):
    """
    Компонент по поиску лица, вырезание области лица и возвращение numpy.ndarray
    """

    def init(self, params: dict, debug: bool = False):
        self._params = params
        self._debug = debug
        self._filling = self._params['filling']
        self._crop_margin = self._params['crop_margin']
        self._crop_size_width = int(self._params['crop_size_width'])
        self._crop_size_height = int(self._params['crop_size_width'])
        self._face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + params['cascade'])

    @staticmethod
    def _is_filling(original_image: float, cropped_image: float, filling: float) -> bool:
        test_filling = int((cropped_image / original_image) * 100)
        return test_filling >= filling

    def cropping(self, image: np.ndarray) -> Tuple[np.ndarray, list]:
        faces = self._face_cascade.detectMultiScale(image, scaleFactor=1.2, minNeighbors=5)
        messages = []
        if len(faces) > 1:
            messages.append('only_one_face')
        elif len(faces) == 1:
            face = faces[0]
            x, y, w, h = face
            original_image = image.shape[0] * image.shape[1]
            cropped_image = h * w
            if not self._is_filling(original_image, cropped_image, self._filling):
                messages.append('come_closer')
                return np.array([]), messages
            x_center = x + (w // 2)
            y_center = y + (h // 2)
            min_dist_to_center = min(x_center,y_center, image.shape[1]-x_center, image.shape[0]-y_center)
            desired_radius = w//2 * self._crop_margin
            if desired_radius > min_dist_to_center:
                messages.append('too_close')
                return np.array([]), messages
            cropped = image[y:y+h, x:x+w]     
            small = cv2.resize(
                cropped, 
                (self._crop_size_width, self._crop_size_height), 
                interpolation=cv2.INTER_LINEAR
                )
            return small, messages
        return np.array([]), messages
