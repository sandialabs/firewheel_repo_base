from base_objects import VMEndpoint

from firewheel.control.experiment_graph import AbstractPlugin


class SendMiniwebArp(AbstractPlugin):
    """
    This plugin adds a call to ping for all :py:class:`VMEndpoints <base_objects.VMEndpoint>`.

    This allows miniweb to determine and display the VM's IP on this interface
    before the experiment is configured (i.e., reaches positive time). Essentially,
    this sends ARP packets which assist miniweb.

    The ping command is generic and works on both Windows and Linux systems.
    The address being pinged is ``192.0.2.1`` which is in a range used for
    examples [#]_. The output is redirected to a file called ``NULL`` to prevent
    expected errors from showing up in the ``vm_resource_logs``.

    .. [#] https://en.wikipedia.org/wiki/Reserved_IP_addresses
    """

    def run(self):
        """
        Schedule the ping command on all VMs.
        """
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(VMEndpoint):
                try:
                    args = "-w 1 192.0.2.1 > NULL"
                    vertex.run_executable(-1, "ping", arguments=args)
                except AttributeError:
                    pass
