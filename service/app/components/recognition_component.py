import cv2
import os
import numpy as np


class RecognitionComponent:
    """
    Компонент по распознованию лица, возвращает ID сотрудника
    """

    _params = None

    def init(self, params: dict):
        self._params = params

    def recognition(self, image: np.ndarray) -> (int, list):
        if len(image) == 0:
            return 0, []

        return 1, ['test success']
