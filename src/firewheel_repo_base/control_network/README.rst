.. _control_network_mc:

###############
control_network
###############

This MC creates a control network within the FIREWHEEL experiment.
Essentially, it connects all VMs in the experiment to a single network with the ``172.16.0.0/16`` IP space and adds the :ref:`cluster-control-node` to this network with an IP address of ``172.16.255.254/16``.
Using this MC, users can take advantage of the :ref:`helper_ssh` and :ref:`helper_scp` helpers.

**Attribute Provides:**
    * ``control_network``

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: control_network_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
