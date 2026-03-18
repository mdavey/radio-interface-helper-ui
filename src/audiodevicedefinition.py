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
    def _get_pw_dump(force_refresh=False) -> PipeWireDump:
        """
        There's logic that says it should always refresh.  Who knows what the user is plugging in and removing while
        running this program?
        """
        if not hasattr(AudioDeviceDefinition, '._pwd') or force_refresh:
            AudioDeviceDefinition._pwd = PipeWireDump()
            AudioDeviceDefinition._pwd.refresh()
        return AudioDeviceDefinition._pwd

    def get_sink_id(self) -> int:
        return self._get_pw_dump().get_node_id_by_name(self.sink)

    def get_source_id(self) -> int:
        return self._get_pw_dump().get_node_id_by_name(self.source)

    @staticmethod
    def _set_volume(node_id: int, volume: float) -> None:
        subprocess.run(["wpctl", "set-volume", str(node_id), str(volume)])

    def set_sink_volume(self) -> None:
        self._set_volume(self.get_sink_id(), self.sink_volume)

    def set_source_volume(self) -> None:
        self._set_volume(self.get_source_id(), self.source_volume)
        pass

    @staticmethod
    def _set_default(node_id: int) -> None:
        subprocess.run(["wpctl", "set-default", str(node_id)])

    def set_as_default(self):
        self._set_default(self.get_sink_id())
        self._set_default(self.get_source_id())


if __name__ == '__main__':
    pwd = PipeWireDump()
    pwd.refresh()

    for name in pwd.get_node_names():
        print("{} - {}".format(pwd.get_node_id_by_name(name), name))
