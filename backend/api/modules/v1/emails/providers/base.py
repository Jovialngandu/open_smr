from abc import ABC, abstractmethod

class EmailProvider(ABC):
    @abstractmethod
    def send(self, subject: str, body_html: str, body_text: str, from_email: str, recipient_list: list) -> bool:
        """
        Méthode standard que chaque provider doit implémenter.
        """
        pass