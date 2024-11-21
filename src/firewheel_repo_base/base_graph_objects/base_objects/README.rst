.. _base_objects_mc:

############
base_objects
############

This Model Component contains many of the basic objects necessary to create an experiment using FIREWHEEL.
Most importantly, this includes basic objects which create VMs (e.g. :py:class:`VMEndpoint <base_objects.VMEndpoint>`), :py:class:`Switch <base_objects.Switch>`, graph :py:class:`Edges <firewheel.control.experiment_graph.Edge>` in the networks (e.g. :py:class:`QoSEdge <base_objects.QoSEdge>`) and various :py:class:`ScheduleEntry <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>` objects.
Therefore, this MC will likely be depended on by most FIREWHEEL topologies.

*****************
Available Objects
*****************

.. automodule:: base_objects
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
