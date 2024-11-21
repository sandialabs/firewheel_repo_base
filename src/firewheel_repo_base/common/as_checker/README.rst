.. _as.checker_mc:

##########
as.checker
##########

This MC helps verify that there are no collisions between `Autonomous System (AS) <https://en.wikipedia.org/wiki/Autonomous_system_(Internet)>`__ numbers in a given experiment.
If there is a collision, a :py:exc:`RuntimeError` is thrown.
This MC assumes that all routers are decorated as a :py:class:`GenericRouter <generic_vm_objects_mc.GenericRouter>`.


**Attribute Depends:**
    * ``topology``


**Attribute Provides:**
    * ``unique_as_nums``


**Model Component Dependencies:**
    * :ref:`generic_vm_objects_mc`


******
Plugin
******

.. automodule:: as.checker_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__


