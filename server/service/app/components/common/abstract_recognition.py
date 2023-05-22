import numpy as np
from abc import ABC, abstractmethod
from app.components.repositories.db_repository_mysql import DBRepository


class Interface(ABC):
    """
    Абстрактный класс по распознованию лица, возвращает ID сотрудника
    """

    @abstractmethod
    def init(self, params: dict, db_repository: DBRepository, debug: bool):
        pass

    @abstractmethod
    def recognition(self, image: np.ndarray) -> (int, list):
        pass

    @abstractmethod
    def get_face_encodings(self, image: np.ndarray) -> (np.array, list):
        pass
