from netaddr import IPNetwork
from base_objects import Switch, VMEndpoint

from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class InsertControlNetwork(AbstractPlugin):
    """Create a "Control" network which provides access to all VMs within an experiment.

    This standard network uses the ``172.16.0.0/16`` IP space. Therefore, if you use this MC,
    your experiment should NOT use this IP space for standard communication.

    Note:
        This potentially provides access for VMs to communicate with your physical compute nodes.
        The :ref:`cluster-control-node` will have the IP address ``172.16.255.254``.
    """

    def _get_next_ip(self):
        """Get the next IP address in the control subnet.

        Returns:
            netaddr.IPAddress: The next valid IP address.
        """
        while True:
            candidate = next(self.ctrl_subnet_addrs)
            if candidate not in self.ctrl_fixed_addrs:
                return candidate

    def run(self):
        """
        Add a control network switch and connect every
        :py:class:`VMEndpoint <base_objects.VMEndpoint>` to that switch.
        """

        # Initialize a few variables
        self.ctrl_subnet = IPNetwork("172.16.0.0/16")
        self.g.control_net = {}
        self.g.control_net["network"] = self.ctrl_subnet
        self.g.control_net["name"] = "CTRLNET"
        self.ctrl_subnet_addrs = self.ctrl_subnet.iter_hosts()

        self.ctrl_host_addr = self.ctrl_subnet[-2]  # This is address 172.16.255.254
        self.g.control_net["host_addr"] = (
            f"{self.ctrl_host_addr}/{self.ctrl_subnet.prefixlen}"
        )

        # skip the first address in case someone wants to use a dhcp server.
        self.ctrl_fixed_addrs = [self.ctrl_subnet[1], self.ctrl_host_addr]

        switch = Vertex(self.g, self.g.control_net["name"])
        switch.decorate(Switch)
        switch.host_address = {
            "ip": self.ctrl_host_addr,
            "netmask": self.ctrl_subnet.netmask,
        }

        connection_counter = 0
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(VMEndpoint):
                ip_addr = self._get_next_ip()
                vertex.control_ip = ip_addr
                vertex.connect(
                    switch, ip_addr, self.ctrl_subnet.netmask, control_network=True
                )
                connection_counter += 1
        self.log.debug("Connected %d endpoints to control network.", connection_counter)
