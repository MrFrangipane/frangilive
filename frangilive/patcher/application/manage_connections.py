from frangilive.devices.domain.audio_port import AudioPort
from frangilive.patcher.domain.audio_connection import AudioConnection
from frangilive.patcher.domain.patcher import Patcher
from frangilive.audio.interfaces.audio_router import AudioRouterGateway


class ManageConnectionsUseCase:
    def __init__(self, router_gateway: AudioRouterGateway, patcher: Patcher):
        self.router_gateway = router_gateway
        self.patcher = patcher

    def connect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        source = self.patcher.device_library.get_instrument(source_name)
        target = self.patcher.device_library.get_instrument(target_name)

        if not source or not target:
            return False

        source_port = source.get_output(source_port_name)
        target_port = target.get_input(target_port_name)

        connection = AudioConnection(source, source_port, target, target_port)
        if connection in self.patcher.connections:
            return False

        self._connect_ports(source_port, target_port)
        self.patcher.add_connection(connection)
        return True

    def disconnect(self, source_name: str, source_port_name: str, target_name: str, target_port_name: str) -> bool:
        source = self.patcher.device_library.get_instrument(source_name)
        target = self.patcher.device_library.get_instrument(target_name)

        if not source or not target:
            return False

        source_port = source.get_output(source_port_name)
        target_port = target.get_input(target_port_name)

        connection = AudioConnection(source, source_port, target, target_port)
        if connection not in self.patcher.connections:
            return False

        self._disconnect_ports(source_port, target_port)
        self.patcher.remove_connection(connection)
        return True

    def _connect_ports(self, source_port: AudioPort, target_port: AudioPort) -> None:
        if source_port.is_stereo:
            if target_port.is_stereo:
                self.router_gateway.connect(source_port.left, target_port.left)
                self.router_gateway.connect(source_port.right, target_port.right)
            else:
                self.router_gateway.connect(source_port.left, target_port.left)
                self.router_gateway.connect(source_port.right, target_port.left)
        else:
            if target_port.is_stereo:
                self.router_gateway.connect(source_port.left, target_port.left)
                self.router_gateway.connect(source_port.left, target_port.right)
            else:
                self.router_gateway.connect(source_port.left, target_port.left)

    def _disconnect_ports(self, source_port: AudioPort, target_port: AudioPort) -> None:
        if source_port.is_stereo:
            if target_port.is_stereo:
                self.router_gateway.disconnect(source_port.left, target_port.left)
                self.router_gateway.disconnect(source_port.right, target_port.right)
            else:
                self.router_gateway.disconnect(source_port.left, target_port.left)
                self.router_gateway.disconnect(source_port.right, target_port.left)
        else:
            if target_port.is_stereo:
                self.router_gateway.disconnect(source_port.left, target_port.left)
                self.router_gateway.disconnect(source_port.left, target_port.right)
            else:
                self.router_gateway.disconnect(source_port.left, target_port.left)

    def clear_all_connections(self) -> None:
        self.router_gateway.remove_all_connections()
        self.patcher.connections.clear()
