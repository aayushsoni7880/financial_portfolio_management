from abc import ABC, abstractmethod


class SentMail(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def sent_mail(self, MailHandlerRequest):
        pass
