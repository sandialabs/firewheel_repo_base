.. _tests.reboot_mc:

############
tests.reboot
############

Add an VM resource to each VM which will reboot the system and test if it works as expected.
The user can pass in the type of reboot they would like to trigger either ``exit_code`` or ``flag`` as the parameter to the Plugin.
This MC is mainly useful for functional testing of FIREWHEEL and as an example of how users can reboot VMs using VMRs.

To learn more about triggering reboots with VMRs see :ref:`vmr-rebooting`.

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: tests.reboot_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
