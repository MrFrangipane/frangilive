from frangilive.cues.domain.cue import Cue
from frangilive.cues.domain.cue_list import CueList
from frangilive.patcher.domain.patcher import Patcher
from frangilive.patcher.application.manage_connections import ManageConnectionsUseCase


class ManageCuesUseCase:
    """
    Use case for managing the cue list, storing patches into cues,
    and switching active patches between cues.
    Later, this use case will also coordinate sending MIDI program changes
    and device states upon cue activation.
    """

    def __init__(
        self,
        cue_list: CueList,
        manage_connections: ManageConnectionsUseCase,
        patcher: Patcher,
    ):
        self.cue_list = cue_list
        self.manage_connections = manage_connections
        self.patcher = patcher

    def create_cue_from_current_patch(self, name: str | None = None) -> Cue:
        """Creates a new cue containing the current patcher connections and activates it."""
        current_conns = list(self.patcher.connections)
        return self.cue_list.create_cue_from_connections(current_conns, name=name)

    def save_current_patch_to_current_cue(self) -> Cue | None:
        """Saves current patcher connections into the currently active cue."""
        current_conns = list(self.patcher.connections)
        return self.cue_list.save_current_cue(current_conns)

    def empty_patch(self) -> None:
        """Clears all audio connections in the active patch and router."""
        self.manage_connections.empty_patch()

    def go_to_first_cue(self) -> Cue | None:
        """Switches to the first cue and loads its patch."""
        cue = self.cue_list.go_to_first_cue()
        if cue is not None:
            self.manage_connections.apply_connections(cue.connections)
        return cue

    def go_to_next_cue(self) -> Cue | None:
        """Switches to the next cue and loads its patch."""
        cue = self.cue_list.go_to_next_cue()
        if cue is not None:
            self.manage_connections.apply_connections(cue.connections)
        return cue

    def go_to_previous_cue(self) -> Cue | None:
        """Switches to the previous cue and loads its patch."""
        cue = self.cue_list.go_to_previous_cue()
        if cue is not None:
            self.manage_connections.apply_connections(cue.connections)
        return cue

    def go_to_cue(self, index: int) -> Cue | None:
        """Switches to the cue at the specified index and loads its patch."""
        cue = self.cue_list.go_to_cue(index)
        if cue is not None:
            self.manage_connections.apply_connections(cue.connections)
        return cue

    def delete_cue(self, index: int | None = None) -> Cue | None:
        """
        Deletes the cue at the specified index or the current active cue.
        Loads the newly active cue's connections if any cue remains,
        or empties the patch if no cues remain.
        """
        target_idx = self.cue_list.current_index if index is None else index
        if target_idx is None:
            return None
        removed = self.cue_list.remove_cue(target_idx)
        if removed is not None:
            current_cue = self.cue_list.current_cue
            if current_cue is not None:
                self.manage_connections.apply_connections(current_cue.connections)
            else:
                self.manage_connections.empty_patch()
        return removed

    def delete_current_cue(self) -> Cue | None:
        """Deletes the current active cue."""
        return self.delete_cue()

    def remove_cue(self, index: int) -> Cue | None:
        """Removes the cue at the specified index."""
        return self.delete_cue(index)
