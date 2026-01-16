from abc import ABC, abstractmethod
from frangilive.domain.models.device_library import DeviceLibrary


class DeviceRepository(ABC):
    @abstractmethod
    def load_library(self) -> DeviceLibrary:
        pass
