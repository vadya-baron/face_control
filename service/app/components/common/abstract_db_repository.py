from abc import ABC, abstractmethod


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
