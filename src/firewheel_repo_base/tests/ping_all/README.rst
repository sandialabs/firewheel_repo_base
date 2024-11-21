.. _tests.ping_all_mc:

##############
tests.ping_all
##############

Intended for use with functionality tests, this MC performs a layer-3 connectivity test via ping.

It adds the ``ping_all.py`` VMR at ``time=30`` to ping every IP address in the experiment from every node within the experiment.
This essentially tests full layer-3 connectivity.

It assumes the presence of a topology with a fully-connected network.
Therefore, there is no handling of unusual or unexpected conditions in the graph, such as disjoint subgraphs.
Additionally, this assumes that Python is installed on the VMs and that a Windows or Unix-based ping program are installed.
This will work with either IPv4 or IPv6 addresses.

If the ``include_routers`` parameter is ``"False"`` (the current default), then routers will be excluded from the test; they will not be pinged or pinging.

**Attribute Provides:**
    * ``ping_all``

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`
    * :ref:`generic_vm_objects_mc`

******
Plugin
******

.. automodule:: tests.ping_all_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
