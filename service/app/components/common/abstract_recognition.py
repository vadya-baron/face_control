import numpy as np
from abc import ABC, abstractmethod


class Interface(ABC):
    """
    Абстрактный класс по распознованию лица, возвращает ID сотрудника
    """

    @abstractmethod
    def init(self, params: dict, debug: bool):
        pass

    @abstractmethod
    def recognition(self, image: np.ndarray) -> (int, list):
        pass
