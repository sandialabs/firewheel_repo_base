.. _minimega.configure_ips_mc:

######################
minimega.configure_ips
######################

This MC ensures that, default gateways are set and if any VM types have a special method of configuring their IP addresses, those actions should be scheduled now.
For example, Linux hosts have a different way of configuring/setting IP addresses than Windows hosts.
Therefore, the :py:class:`LinuxHost <linux.base_objects.LinuxHost>` class has implemented a :py:meth:`configure_ips <linux.base_objects.LinuxHost.configure_ips>` method to add a VMR which correctly configures the VMs IPs.
This MC calls the ``configure_ips`` method for all :py:class:`Vertexes <firewheel.control.experiment_graph.Vertex>` and ignores errors when a :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` can't call that method.

**Attribute Provides:**
    * ``ips``

**Attribute Depends:**
    * ``mac_addresses``

******
Plugin
******

.. automodule:: minimega.configure_ips_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
