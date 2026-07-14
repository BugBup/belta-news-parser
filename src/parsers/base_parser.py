# src/parsers/base_parser.py

from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Базовый класс для всех парсеров"""
    
    def __init__(self, source_config):
        self.source = source_config
        self.items = []
        
    @abstractmethod
    def fetch_data(self):
        """Метод для получения данных из источника"""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data):
        """Метод для парсинга полученных данных"""
        pass
    
    def get_items(self):
        """Возвращает список спарсенных элементов"""
        return self.items
