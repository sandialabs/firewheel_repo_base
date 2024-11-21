.. _tests.vm_gen_mc:

############
tests.vm_gen
############

This MC will create an arbitrary number of :py:class:`Ubuntu2204Server <linux.ubuntu2204.Ubuntu2204Server>` VMs.
The user can pass in the number as the parameter to the Plugin.
The new VMs will be give the name ``server-X`` where ``X`` is an incrementing integer.

.. Note::
    The VMs will *not* be connected in any way.

**Attribute Provides:**
    * ``topology``

**Attribute Depends:**
    * ``graph``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`
    * :ref:`linux.ubuntu1604_mc`

******
Plugin
******

.. automodule:: tests.vm_gen_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__

