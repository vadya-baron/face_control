from abc import ABC, abstractmethod
import numpy as np


class Interface(ABC):
    """
    Абстрактный класс репозитория. Для учета посещаемости сотрудников
    """

    @abstractmethod
    def init(self, conn, params: dict, debug: bool):
        pass

    @abstractmethod
    def add_visit(self, employee_id: int, direction: int) -> int:
        pass

    @abstractmethod
    def get_last_visit(self, employee_id: int, filters: dict) -> dict:
        pass

    @abstractmethod
    def get_visits(self, filters: dict) -> list[dict]:
        pass

    @abstractmethod
    def get_start_end_working(self, for_date: str = None) -> (list[dict], list[dict]):
        pass

    @abstractmethod
    def get_employees(self, filters: dict = None) -> list[dict]:
        pass

    @abstractmethod
    def add_employee(self, model: dict) -> dict:
        pass

    @abstractmethod
    def remove_employee(self, id: int) -> bool:
        pass

    @abstractmethod
    def update_status_employee(self, id: int, status: int) -> bool:
        pass

    @abstractmethod
    def add_vectors(self, id: int, face_vector: np.ndarray, face_recognize_vector: np.array) -> bool:
        pass

    @abstractmethod
    def get_vectors(self, persons_ids: list) -> list[dict]:
        pass
