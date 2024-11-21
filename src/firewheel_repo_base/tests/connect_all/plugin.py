import netaddr
from base_objects import Switch, VMEndpoint

from firewheel.lib.utilities import strtobool
from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Connect all VMs in the experiment to a single :py:class:`Switch <base_objects.Switch>`.
    This is for testing connectivity, NIC creation, and IP address assignment.
    """

    def run(self, num_nets="1", ipv6="False"):
        """
        Connect all VMs in the experiment to a single :py:class:`Switch <base_objects.Switch>`.
        The number of connections depends on the number of networks passed into the
        plugin. An error will be thrown if there are more than 255 networks.

        Args:
            num_nets (str): The number of networks to connect.
            ipv6 (str): A string representing whether or not to use IPv6 networking.

        Raises:
            RuntimeError: If ``num_nets`` is less than or equal to 0 or greater than 255.
        """

        num_nets = int(num_nets)
        ipv6 = strtobool(ipv6)

        if num_nets >= 255 or num_nets <= 0:
            raise RuntimeError("The number of networks must be between [1-254].")

        if num_nets >= 10:
            scaling_factor = num_nets // 20 + 1
            for v in self.g.get_vertices():
                if v.is_decorated_by(VMEndpoint):
                    try:
                        v.vm["mem"] = 1024 * scaling_factor
                        v.vm["vcpu"] = {"sockets": 4, "cores": 1, "threads": 1}
                    except AttributeError:
                        v.vm = {"mem": 1024 * scaling_factor}
                        v.vm["vcpu"] = {"sockets": 4, "cores": 1, "threads": 1}
        for net in range(1, num_nets + 1):
            # Create our switch
            switch = Vertex(self.g, f"switch-{net}")
            switch.decorate(Switch)

            # Create an IP Address
            if ipv6:
                network = netaddr.IPNetwork(f"{net}::/16")
            else:
                network = netaddr.IPNetwork(f"{net}.0.0.0/8")
            ips = network.iter_hosts()

            for v in self.g.get_vertices():
                if v.is_decorated_by(VMEndpoint):
                    v.connect(switch, next(ips), network.netmask)
