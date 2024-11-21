.. misc.networkx documentation file, created by FIREWHEELs Model Component generation.
   You can adapt this file completely to your liking.

.. _misc.networkx_mc:

#############
misc.networkx
#############

This Model Component provides functions and objects that make it easier to convert a NetworkX graph into a FIREWHEEL :py:class:`ExperimentGraph`.
Specifically, this is useful when using `NetworkX Graph Generators <https://networkx.org/documentation/stable/reference/generators.html>`_.
This MC will only help build out a basic :py:class:`ExperimentGraph` and it is left to the users to then decorate the :py:class:`Vertecies <Vertex>` and create "real" edges based on the outline provided.

**Attribute Depends:**
    * ``graph``


**Model Component Depends:**
    * ``base_objects``

*******
Example
*******

The example shown below is a ``plugin.py`` file for converting :py:func:`networkx.generators.classic.star_graph` into a FIREWHEEL topology.
This is intentionally a simple example.
A more complex example, provided in :ref:`tests.networkx_mc`, shows how users can make use of the :py:func:`networkx.random_internet_as_graph` topology.

.. code-block:: python

    import netaddr
    import networkx as nx
    from misc.networkx import convert_nx_to_fw
    from linux.ubuntu2204 import Ubuntu2204Server

    from firewheel.control.experiment_graph import Vertex, AbstractPlugin

    from base_objects import Switch


    class Plugin(AbstractPlugin):
        """
        This plugin provides an example of how to convert a NetworkX
        based graph into a FIREWHEEL experiment.
        """

        def run(self, num_nodes="10"):
            """
            This example creates a NetworkX star network and converts it into a FIREWHEEL topology.
            In this case the center of the Star will be a Switch and all the other nodes will
            be Ubuntu servers.

            Args:
                num_nodes (str): Signifies the number of nodes in the network.
                    This should be convertible to an :py:data:`int`.

            Raises:
                RuntimeError: If the input parameters are improperly formatted.
            """

            # Catch any issues with input parameters
            try:
                num_nodes = int(num_nodes)
            except (TypeError, ValueError) as exc:
                raise RuntimeError("The number of nodes should be an integer") from exc

            # Create the star graph with the specified number of nodes
            nx_net = nx.star_graph(num_nodes)

            # Convert the NetworkX graph to FIREWHEEL Vertecies/Edges
            convert_nx_to_fw(nx_net, self.g)

            # In this topology, node labels are 0 to `num_nodes` with the center
            # being 0. In this case, we can make that center node a Switch and
            # then all the other nodes Ubuntu servers.
            switch = self.g.find_vertex_by_id(0)
            switch.name = "center-switch"
            switch.decorate(Switch)

            # Create a network for the VMs to communicate
            network = netaddr.IPNetwork("10.0.0.0/8")
            ips = network.iter_hosts()

            # We can iterate through all the Vertecies and decorate them.
            # Additionally, let's rename them
            for node in self.g.get_vertices():
                if node.graph_id == 0:
                    continue
                # For each node, rename it and decorate it with the correct
                # VM object
                node.name = f"server-{node.graph_id}"
                node.decorate(Ubuntu2204Server)

                # Connect the Vertex to the Switch
                node.connect(switch, next(ips), network.netmask)


*****************
Available Objects
*****************

.. automodule:: misc.networkx
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__

