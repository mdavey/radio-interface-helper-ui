import subprocess
import json


class PipeWireDump:
    """
    Reads the output of pw-dump and parses out a list of PipeWire:Interface nodes
    """
    def __init__(self):
        self.items = []
        pass

    def refresh(self):
        cmd = subprocess.run(['pw-dump'], check=True, capture_output=True, text=True)
        self.items = json.loads(cmd.stdout)

    def get_nodes(self):
        for item in self.items:
            if item['type'] == 'PipeWire:Interface:Node':
                yield item

    def get_node_names(self):
        for node in self.get_nodes():
            yield node['info']['props']['node.name']

    def get_node_id_by_name(self, name):
        for node in self.get_nodes():
            if node['info']['props']['node.name'] == name:
                return int(node['id'])
        return None