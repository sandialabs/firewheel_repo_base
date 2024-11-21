.. _minimega.testbed_available_mc:

##########################
minimega.testbed_available
##########################

This model component is responsible for ensuring that experiments do not collide with each other.
Currently, it uses the :py:class:`minimegaAPI <firewheel.lib.minimega.api.minimegaAPI>` to check if any VMs are running and the :py:mod:`firewheel.vm_resource_manager.api` to check if an experiment launch time has been set.
If either is true, then it is assumed that an experiment is running, and an :py:exc:`ExistingExperimentError <minimega.testbed_available.ExistingExperimentError>` is thrown.
Otherwise, it uses the :py:mod:`firewheel.vm_resource_manager.api` to set the experiment experiment launch time and proceeds launching the experiment.
Note that the launch time (i.e. the time the experiment was kicked off) differs from the :ref:`start-time` (i.e. when the experiment reaches ``time=0``).

**Attribute Provides:**
    * ``testbed_available``

******
Plugin
******

.. automodule:: minimega.testbed_available_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
