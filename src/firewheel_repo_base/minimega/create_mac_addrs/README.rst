.. _minimega.create_mac_addresses_mc:

#############################
minimega.create_mac_addresses
#############################

This MC ensures that each VM has a unique MAC address.
It works by keeping a global counter and incrementing it.
For simplicity, this MC uses `netaddr's EUI library <https://netaddr.readthedocs.io/en/latest/api.html#mac-addresses-and-the-ieee-eui-standard>`_.

Users can optionally pass in an integer to the plugin to seed the starting MAC address.

**Attribute Provides:**
    * ``mac_addresses``

**Attribute Depends:**
    * ``topology``

******
Plugin
******

.. automodule:: minimega.create_mac_addresses_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
