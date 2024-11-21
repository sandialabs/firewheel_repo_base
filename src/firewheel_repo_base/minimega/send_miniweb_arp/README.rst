.. _minimega.send_miniweb_arp_mc:

#########################
minimega.send_miniweb_arp
#########################

This MC adds a call to ping for all VMs.
This allows miniweb to determine and display at least one of the VM's IP addresses before the experiment is configured (i.e., reaches positive time).
Essentially, this sends ARP packets which assist miniweb.

The ping command is generic and works on both Windows and Linux systems.
The address being pinged is ``192.0.2.1`` which is in a range used for examples [#]_.
The output is redirected to a file called ``NULL`` to prevent expected errors from showing up in the log files.

.. [#] https://en.wikipedia.org/wiki/Reserved_IP_addresses

**Attribute Provides:**
    * ``sent_arp``

**Attribute Depends:**
    * ``ips``

******
Plugin
******

.. automodule:: minimega.send_miniweb_arp_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
