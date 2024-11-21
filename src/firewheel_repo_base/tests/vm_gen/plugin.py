from linux.ubuntu2204 import Ubuntu2204Server

from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class VmGen(AbstractPlugin):
    """
    This plugin will create as many
    :py:class:`Ubuntu2204Server <linux.ubuntu2204.Ubuntu2204Server>` VMs as the size specifies.
    The new VMs will be give the name server-X where X is an integer.
    """

    def run(self, size="1"):
        """
        This plugin will create as many
        :py:class:`Ubuntu2204Server <linux.ubuntu2204.Ubuntu2204Server>` VMs as the size specifies.

        Args:
            size (str): The number of VMs to create.
        """
        size = int(size)

        for i in range(size):
            vm = Vertex(self.g, f"server-{i}")
            vm.decorate(Ubuntu2204Server)
