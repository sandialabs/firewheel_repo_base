.. _tests.connect_all_mc:

#################
tests.connect_all
#################

Connect all VMs in the experiment to a single :py:class:`Switch <base_objects.Switch>`.
The primary use is to test connectivity, NIC creation, and IP address assignment.
This MC can support up to 255 networks where all VMs would be connected to each network.
If more than 10 networks are used, the VMs RAM and number of cores are also increased.
This is due to issues within VMs handling large numbers of NICs.
This MC also supports both IPv4 and IPv6 networks.

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: tests.connect_all_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
