from abc import ABC, abstractmethod
from frangilive.devices.domain.device_library import DeviceLibrary


class DeviceRepository(ABC):
    @abstractmethod
    def load_library(self) -> DeviceLibrary:
        pass
