from abc import ABC, abstractmethod
from typing import List

class IComposingWorker(ABC):
    @abstractmethod
    def find_jobs(self) -> List[str]:
        pass

    @abstractmethod
    def process_book(self, book_id: str) -> bool:
        pass

    @abstractmethod
    def run(self):
        pass 