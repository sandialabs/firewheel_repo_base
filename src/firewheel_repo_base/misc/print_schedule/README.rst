.. _misc.print_schedule_mc:

###################
misc.print_schedule
###################

This MC outputs a JSON representation of the entire experiment's :ref:`vm-resource-schedule`.
If a filename is passed into the Plugin, then the JSON is written to a file; otherwise, it will print the schedule to ``stdout``.
This JSON is useful for analyzing the expected experiment schedule and reviewing inputs for the various involved VM resources.
This output does **NOT** include associated VM resource scripts nor binary files to reduce file size.

This MC can be placed in multiple locations of the experiment pipeline so that users can see different views of how the experiment schedule is evolving.

.. warning::

    In cases where a complete schedule is the desired output, this MC must be the **last** parameter to :ref:`helper_experiment`.
    For example, ``firewheel experiment tests.vm_gen minimega.launch misc.print_schedule``

**Attribute Depends:**
    * ``graph``

******
Plugin
******

.. automodule:: misc.print_schedule_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
