from dataclasses import dataclass, field
from .audio_connection import AudioConnection
from frangilive.devices.domain.device_library import DeviceLibrary


class CyclicConnectionError(ValueError):
    """Raised when adding an audio connection would create a cycle in the connection graph."""
    pass


@dataclass
class Patcher:
    device_library: DeviceLibrary
    connections: list[AudioConnection] = field(default_factory=list)

    def __post_init__(self):
        if not self.is_acyclic():
            raise CyclicConnectionError("Initial connection graph contains a cycle.")

    def is_acyclic(self) -> bool:
        """Check whether the current connection graph is a directed acyclic graph (DAG)."""
        return self._check_acyclic(self.connections)

    def has_cycle(self) -> bool:
        """Check whether the current connection graph contains any cycles."""
        return not self.is_acyclic()

    def would_create_cycle(self, connection: AudioConnection) -> bool:
        """Check if adding the given connection would introduce a cycle."""
        if connection.source_instrument.name == connection.target_instrument.name:
            return True
        if connection in self.connections:
            return False
        return not self._check_acyclic(self.connections + [connection])

    def can_add_connection(self, connection: AudioConnection) -> bool:
        """Check if the connection can be safely added without violating acyclicity."""
        return not self.would_create_cycle(connection)

    def would_create_cycle_between(self, source_name: str, target_name: str) -> bool:
        """Check if adding an edge from source_name to target_name would introduce a cycle."""
        if source_name == target_name:
            return True
        if any(c.source_instrument.name == source_name and c.target_instrument.name == target_name for c in self.connections):
            return False

        adj: dict[str, list[str]] = {}
        nodes: set[str] = {source_name, target_name}
        for c in self.connections:
            src = c.source_instrument.name
            tgt = c.target_instrument.name
            if src == tgt:
                return True
            nodes.add(src)
            nodes.add(tgt)
            if src not in adj:
                adj[src] = []
            adj[src].append(tgt)

        if source_name not in adj:
            adj[source_name] = []
        adj[source_name].append(target_name)

        state: dict[str, int] = {}

        def dfs(node: str) -> bool:
            state[node] = 1
            for neighbor in adj.get(node, []):
                st = state.get(neighbor, 0)
                if st == 1:
                    return False
                if st == 0:
                    if not dfs(neighbor):
                        return False
            state[node] = 2
            return True

        for node in nodes:
            if state.get(node, 0) == 0:
                if not dfs(node):
                    return True

        return False

    def add_connection(self, connection: AudioConnection):
        if connection in self.connections:
            return
        if self.would_create_cycle(connection):
            raise CyclicConnectionError(
                f"Cannot add connection from '{connection.source_instrument.name}' "
                f"to '{connection.target_instrument.name}': would create a cycle in the connection graph."
            )
        self.connections.append(connection)

    def remove_connection(self, connection: AudioConnection):
        if connection in self.connections:
            self.connections.remove(connection)

    def get_connections_between(self, source_name: str, target_name: str) -> list[AudioConnection]:
        return [
            c for c in self.connections
            if c.source_instrument.name == source_name and c.target_instrument.name == target_name
        ]

    @staticmethod
    def _check_acyclic(connections: list[AudioConnection]) -> bool:
        adj: dict[str, list[str]] = {}
        nodes: set[str] = set()

        for c in connections:
            src = c.source_instrument.name
            tgt = c.target_instrument.name
            if src == tgt:
                return False
            nodes.add(src)
            nodes.add(tgt)
            if src not in adj:
                adj[src] = []
            adj[src].append(tgt)

        # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
        state: dict[str, int] = {}

        def dfs(node: str) -> bool:
            state[node] = 1
            for neighbor in adj.get(node, []):
                st = state.get(neighbor, 0)
                if st == 1:
                    return False
                if st == 0:
                    if not dfs(neighbor):
                        return False
            state[node] = 2
            return True

        for node in nodes:
            if state.get(node, 0) == 0:
                if not dfs(node):
                    return False

        return True
