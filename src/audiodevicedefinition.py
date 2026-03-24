import subprocess
from dataclasses import dataclass
from src.pipewiredump import PipeWireDump


@dataclass
class AudioDeviceDefinition:
    """
    This is a helper class to abstract talking to the OS about the audio devices
    We are working with both a Sink (speaker) and Source (microphone) device as a pair
    Is uses the PipeWireDump (pw-dump) to turns PipeWire node names into ids at runtime
    And wp-ctl to set volumes and default devices
    """
    sink: str
    source: str
    sink_volume: float
    source_volume: float
    sink_id: int = None
    source_id: int = None

    @staticmethod
    def _set_volume(node_id: int, volume: float) -> None:
        subprocess.run(["wpctl", "set-volume", str(node_id), str(volume)])

    @staticmethod
    def _set_default(node_id: int) -> None:
        subprocess.run(["wpctl", "set-default", str(node_id)])

    def switch(self) -> bool:
        pwd = PipeWireDump()
        pwd.refresh()

        sink_id   = pwd.get_node_id_by_name(self.sink)
        source_id = pwd.get_node_id_by_name(self.source)

        if sink_id is None or source_id is None:
            return False

        self._set_default(sink_id)
        self._set_default(source_id)

        if self.sink_volume >= 0.0:
            self._set_volume(sink_id, self.sink_volume)

        if self.source_volume >= 0.0:
            self._set_volume(source_id, self.source_volume)

        return True