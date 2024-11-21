import netaddr
from base_objects import Switch
from generic_vm_objects import GenericRouter
from linux.base_objects import LinuxHost

from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class RouterTree(AbstractPlugin):
    """This creates a router high-degree tree running OSPF and BGP.

    Following is an example of a 3 degree tree::

        <host> -- <OSPF> -- <BGP> -------------------------
                                |           |           |
                            <BGP 0>     <BGP 1>     <BGP 2>
                                |           |           |
                            <OSPF 0>    <OSPF 1>    <OSPF 2>
                                |           |           |
                            <host 0>    <host 1>    <host 2>

    """

    def run(self, size):
        """
        Create the router tree topology.

        Args:
            size (str): The degree of the router tree. This must be castable to an :obj:`int`.
        """

        # Convert the size to an int.
        # Note that all parameters to Plugins will be strings as they are passed
        # in via the command line. They have to be converted to the requested type.
        size = int(size)

        # Create two networks where the control nets can be used for communication
        # between routers and the host_nets are used to communicate amongst hosts.
        control_nets = netaddr.IPNetwork("192.168.0.0/16").subnet(30)
        host_nets = netaddr.IPNetwork("10.0.0.0/8").subnet(24)

        # Create an iterator with AS numbers which can be used with the BGP routers.
        # Start with AS number 1000 because there were topologies connected with
        # router_tree that used the same AS numbers.
        start_as_number = 1000
        as_nums = iter(range(start_as_number, start_as_number + size + 1))

        # First, make the root pair.
        root = self._make_router_pair("root.net", control_nets, host_nets, as_nums)

        # The root BGP router needs lots of memory if the topology is large
        try:
            root.vm["mem"] = 4096
        except AttributeError:
            root.vm = {"mem": 4096}

        # Next, create all of the leaves and link them to the root.
        for i in range(size):
            # Create the leaf nodes and return the BGP router
            leaf = self._make_router_pair(
                f"leaf-{i}.net", control_nets, host_nets, as_nums
            )

            # Create a switch to connect the leaf to the root router
            switch = Vertex(self.g, f"root-leaf{i}.switch")
            switch.decorate(Switch)

            # Get the next subnet
            bgp_net = next(control_nets)
            bgp_ips = bgp_net.iter_hosts()

            # Connect both the root BGP router and the leaf BGP router
            leaf.connect(switch, next(bgp_ips), bgp_net.netmask)
            root.connect(switch, next(bgp_ips), bgp_net.netmask)

            # Make sure that the routers peer with each other via BGP
            root.link_bgp(leaf, switch, switch)

            # Sanity check that everything was created correctly
            # i.e. make sure interfaces were created.
            assert len(root.interfaces.interfaces) != 0
            assert len(leaf.interfaces.interfaces) != 0

    def _make_router_pair(self, name, control_nets, host_nets, as_nums):
        """Internal function to create the host, OSPF, BGP sequence.

        Args:
            name (str): The name of the router/host sequence (e.g. 'leaf-1.net').
            control_nets (netaddr.IPNetwork): The network to use between routers.
            host_nets (netaddr.IPNetwork): The network to use between hosts.
            as_nums (range_iterator): An iterator for the AS numbering of the BGP routers.

        Returns:
            generic_vm_objects.GenericRouter: The BGP router for the pairing.
        """

        # Get the next subnet in the `host_nets` IP block
        # Then get an iter of IPs for that subnet
        host_net = next(host_nets)
        host_ips = host_net.iter_hosts()

        # Create a host
        host = Vertex(self.g, f"host.{name}")
        host.decorate(LinuxHost)

        # Create an OSFF Router
        ospf = Vertex(self.g, f"ospf.{name}")
        ospf.decorate(GenericRouter)

        # Create a switch to connect the Host and OSPF router
        switch_host_to_ospf = Vertex(self.g, f"switch-host-ospf.{name}")
        switch_host_to_ospf.decorate(Switch)

        # Connect the OSPF router and Host to the Switch.
        # Use the `host_nets` IP network as the IP address for the VMs
        ospf.connect(switch_host_to_ospf, next(host_ips), host_net.netmask)
        host.connect(switch_host_to_ospf, next(host_ips), host_net.netmask)

        # Get the next subnet in the `control_nets` IP block
        # Then get an iter of IPs for that subnet
        ospf_net = next(control_nets)
        ospf_ips = ospf_net.iter_hosts()

        # Create a BGP Router
        bgp = Vertex(self.g, f"bgp.{name}")
        bgp.decorate(GenericRouter)

        # Set the AS number of the BGP router
        as_num = next(as_nums)
        bgp.set_bgp_as(as_num)

        # Create a switch to connect the OSPF router and the BGP router
        switch_ospf_to_bgp = Vertex(self.g, f"switch-ospf-bgp.{name}")
        switch_ospf_to_bgp.decorate(Switch)

        # Connect the OSPF and BGP routers to the Switch.
        # We use the ospf_connect method which enables us to define the connection
        # as an OSPF connection.
        # Use the `control_nets` IP network as the IP address for the VMs
        ospf.ospf_connect(switch_ospf_to_bgp, next(ospf_ips), ospf_net.netmask)
        bgp.ospf_connect(switch_ospf_to_bgp, next(ospf_ips), ospf_net.netmask)

        # Redistribute routes for directly connected subnets to OSPF peers.
        ospf.redistribute_ospf_connected()

        # Enable redistributing routes from BGP peers to OSPF peers.
        bgp.redistribute_bgp_into_ospf()

        # Enable redistributing routes from OSPF peers to BGP peers.
        bgp.redistribute_ospf_into_bgp()

        # Return the BGP router
        return bgp
