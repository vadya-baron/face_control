import numpy as np
from abc import ABC, abstractmethod


class Interface(ABC):
    """
    Абстрактный класс по поиску лица, вырезание области лица и возвращение numpy.ndarray
    """

    @abstractmethod
    def init(self, params: dict, debug: bool):
        pass

    @abstractmethod
    def cropping(self, image: np.ndarray) -> (list, list):
        pass
