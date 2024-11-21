.. _vm_resource.schedule_mc:

####################
vm_resource.schedule
####################

This MC iterates over every :py:class:`VMEndpoint <base_objects.VMEndpoint>` in the experiment graph and gets the VM's schedule (using :py:meth:`base_objects.VmResourceSchedule.get_schedule`.
The MC then adds all the schedules to the :py:class:`ScheduleDb <firewheel.vm_resource_manager.schedule_db.ScheduleDb>` and adds the mapping of the VMs (i.e. the name and UUID) to the :py:class:`VMMapping Database <firewheel.vm_resource_manager.vm_mapping.VMMapping>`.
Lastly, this MC creates a set of all required VMRs which need to be loaded into the experiment.
This set can be used later to ensure that the VMRs have been correctly provided by the MCs in the experiment.

**Attribute Provides:**
    * ``vm_resource_schedule_database``

**Attribute Depends:**
    * ``topology``
    * ``schedules_ready``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: vm_resource.schedule_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
