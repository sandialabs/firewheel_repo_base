import netaddr
import networkx as nx
from base_objects import Switch
from misc.networkx import NxEdge, convert_nx_to_fw
from linux.ubuntu2204 import Ubuntu2204Server
from generic_vm_objects import GenericRouter

from firewheel.lib.utilities import strtobool
from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class Plugin(AbstractPlugin):
    """
    This plugin provides an example of how to convert a NetworkX
    based graph into a FIREWHEEL experiment.
    Specifically, it leverages the :py:func:`nx.random_internet_as_graph`
    topology which creates a random undirected graph resembling the Internet AS network.
    """

    def run(self, num_nodes="100", del_edges="False"):
        """
        Run method documentation which takes the NetworkX graph and
        converts it to FIREWHEEL.

        Args:
            num_nodes (str): Signifies the number of nodes in the network.
                This should be convertible to an :py:data:`int`.
            del_edges (str): Whether to delete any :py:class:`Edges <Edges>`
                that are decorated with :py:class:`NxEdge`. This is particularly
                useful for visualizing the graph structure.
                This should be convertible to an :py:data:`bool`.

        Raises:
            RuntimeError: If the input parameters are improperly formatted.
        """

        # Catch any issues with input parameters
        try:
            num_nodes = int(num_nodes)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("The number of nodes should be an integer") from exc

        del_edges = strtobool(del_edges)

        # Create the random graph with the specified number of nodes
        nx_inet = nx.random_internet_as_graph(num_nodes)

        # Convert the NetworkX graph to FIREWHEEL Vertices/Edges
        convert_nx_to_fw(nx_inet, self.g)

        # Create an iterator with AS numbers which can be used with the BGP routers.
        as_nums = iter(range(1, self.g.g.number_of_nodes() + 1))

        # Each node models an autonomous system, with an attribute 'type'
        # specifying its kind; tier-1 (T), mid-level (M), customer (C) or
        # content-provider (CP).

        # Let's rename the Vertices based on their type
        tier_prefix = "Tier1"
        mid_prefix = "mid-level"
        cus_prefix = "customer"
        for node in self.g.get_vertices():
            # For each node, rename it and decorate it with the correct
            # VM object
            if node.nx_data["type"] == "T":
                node.name = f"{tier_prefix}-{node.graph_id}"
                node.decorate(GenericRouter)
                # Setting the AS number for this router
                node.set_bgp_as(next(as_nums))

            if node.nx_data["type"] == "M":
                node.name = f"{mid_prefix}-{node.graph_id}"
                node.decorate(GenericRouter)
                # Setting the AS number for this router
                node.set_bgp_as(next(as_nums))

            if node.nx_data["type"] == "C" or node.nx_data["type"] == "CP":
                node.name = f"{cus_prefix}-{node.graph_id}"
                node.decorate(Ubuntu2204Server)

        # Create different networks for each layer-3 connection
        # Internet networks, creates 65536 different networks
        inet_networks = netaddr.IPNetwork("1.0.0.0/8").subnet(24)

        # Customer networks, creates 65536 different networks
        customer_networks = netaddr.IPNetwork("2.0.0.0/8").subnet(24)

        # We cannot add new edges while iterating over the existing edges
        # so we will keep track of any edges that need to be added.
        router_edges = []

        # For connections to customers, there should be a single switch (for the network)
        # Therefore, let's use a dictionary for the router to hold all associated customers.
        customer_edges = {}

        # Search of edges that should be modified
        for edge in self.g.get_edges():
            # Ignore non NetworkX edges
            if not edge.is_decorated_by(NxEdge):
                continue

            # Check if both the source and destination are routers
            if edge.source.is_decorated_by(GenericRouter):
                if edge.destination.is_decorated_by(GenericRouter):
                    router_edges.append(edge)
                else:
                    # If the destination is not a router, it must be a customer
                    cust_list = customer_edges.get(edge.source, [])
                    cust_list.append(edge.destination)
                    customer_edges[edge.source] = cust_list
            # If the source is Ubuntu, see if it's peer is a router
            elif edge.source.is_decorated_by(Ubuntu2204Server):
                if edge.destination.is_decorated_by(GenericRouter):
                    cust_list = customer_edges.get(edge.destination, [])
                    cust_list.append(edge.source)
                    customer_edges[edge.source] = cust_list

        # Now we should iterate over all of the edges we should add/modify
        for edge in router_edges:
            vert = edge.source
            neighbor = edge.destination

            # A Switch is needed for this layer-3 edge
            switch = Vertex(self.g, f"switch-{vert.name}-{neighbor.name}")
            switch.decorate(Switch)

            # Get the next available network
            network = next(inet_networks)
            ips = network.iter_hosts()

            # Connect the routers to the switch and link them via BGP
            vert.connect(switch, next(ips), network.netmask)
            neighbor.connect(switch, next(ips), network.netmask)
            vert.link_bgp(neighbor, switch)

        # Iterate over all the routers with customers
        for rtr, neighbor_list in customer_edges.items():
            # A Switch is needed for this layer-3 edge
            switch = Vertex(self.g, f"switch-{rtr.name}-customer")
            switch.decorate(Switch)

            # Get the next available network
            network = next(customer_networks)
            ips = network.iter_hosts()

            # Connect the router to the switch and advertise
            # this network using BGP
            rtr.connect(switch, next(ips), network.netmask)
            rtr.add_bgp_network(network)

            # Connect each of the customers to the switch
            for neighbor in neighbor_list:
                neighbor.connect(switch, next(ips), network.netmask)

        # If we want to remove all NxEdges to better help visualize the graph
        # we can do that now
        if del_edges:
            rm_list = []
            for edge in self.g.get_edges():
                if edge.is_decorated_by(NxEdge):
                    rm_list.append(edge)
            for edge in rm_list:
                edge.delete()
