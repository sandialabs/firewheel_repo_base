.. tests.networkx documentation file, created by FIREWHEELs Model Component generation.
   You can adapt this file completely to your liking.

.. _tests.networkx_mc:

##############
tests.networkx
##############

This MC provides a complex example of how to convert a NetworkX graph into a FIREWHEEL experiment.
Specifically, it leverages the :py:func:`networkx.random_internet_as_graph` topology which creates a random undirected graph resembling the Internet AS network.
In this graph, each node models an autonomous system, with an attribute ``type`` specifying its kind; tier-1 (T), mid-level (M), customer (C) or content-provider (CP).
The associated ``plugin.py`` converts each AS (i.e. ``T`` and ``M``) into a BGP router and each customer (i.e., ``C`` and ``CP``) into a Ubuntu server.
This topology takes users though how to decorate the nodes, add the appropriate BGP information, and insert :py:class:`Switches <base_objects.Switch>` between links so that it will function correctly.
Users can specify the number of nodes in the topology and can also choose to remove the :py:class:`NxEdges <misc.networkx.NxEdge>` to better visualize the graph with the :ref:`misc.print_graph_mc` Model Component.


**Attribute Depends:**
    * ``graph``


**Attribute Provides:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`misc.networkx_mc`
    * :ref:`base_objects_mc`
    * :ref:`generic_vm_objects_mc`
    * :ref:`linux.ubuntu2204_mc`

******
Plugin
******

.. automodule:: tests.networkx_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__


