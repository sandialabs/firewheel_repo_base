.. _vm_resource.validate_mc:

####################
vm_resource.validate
####################

This MC ensures that all VMRs which have been scheduled have been uploaded to the :py:class:`VmResourceStore <firewheel.vm_resource_manager.vm_resource_store.VmResourceStore>`.
If any missing VMRs are identified a :py:class:`MissingRequiredVMResourcesError <firewheel.control.model_component_exceptions.MissingRequiredVMResourcesError>` is raised.

**Attribute Provides:**
    * ``validated_vm_resource_schedule_database``

**Attribute Depends:**
    * ``vm_resource_schedule_database``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: vm_resource.validate_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
