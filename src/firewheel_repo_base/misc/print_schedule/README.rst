.. _misc.print_schedule_mc:

###################
misc.print_schedule
###################

This MC outputs a JSON representation of the experiment graph's :ref:`vm-resource-schedule` at the time the MC is executed.
If a filename is passed into the Plugin, then the JSON is written to a file; otherwise, it will print the schedule to ``stdout``.
This JSON is useful for analyzing the expected experiment schedule and reviewing inputs for the various involved VM resources.
This output does **NOT** include associated VM resource scripts nor binary files to reduce file size.

.. warning::

    In cases where a complete schedule is the desired output, this MC must be the **last** parameter to :ref:`helper_experiment`.
    For example, ``firewheel experiment tests.vm_gen minimega.launch misc.print_schedule``

This MC can be placed in multiple locations of the experiment pipeline so that users can see different views of how the experiment schedule is evolving.
However, the placement of this MC within the experiment may provide a different view than expected as FIREWHEEL resolves various model component dependencies.
Therefore, the output schedule will include all MCs run by FIREWHEEL including explicitly specified and implicitly depended on components up to the point where the schedule is output.
This can even include components that are depended upon by components run *after* :ref:`misc.print_schedule_mc` due to FIREWHEEL's :ref:`dependency_management`.

For example, ``firewheel experiment tests.vm_gen:10 control_network misc.print_schedule minimega.launch`` results in the following output:

.. code-block:: bash
    :emphasize-lines: 17-19

                            Model Components Executed
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
    ┃      Model Component Name       ┃   Result   ┃     Timing     ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
    │ base_objects                    │         OK │  0.013 seconds │
    │ linux.base_objects              │         OK │  0.014 seconds │
    │ linux.ubuntu                    │         OK │  0.012 seconds │
    │ linux.ubuntu2204                │         OK │  0.019 seconds │
    │ misc.blank_graph                │         OK │  0.001 seconds │
    │ tests.vm_gen                    │         OK │  0.003 seconds │
    │ minimega.emulated_entities      │         OK │  0.003 seconds │
    │ minimega.testbed_available      │         OK │  0.021 seconds │
    │ linux.ubuntu1604                │         OK │  0.010 seconds │
    │ generic_vm_objects              │         OK │  0.001 seconds │
    │ vyos                            │         OK │  0.009 seconds │
    │ vyos.helium118                  │         OK │  0.008 seconds │
    │ control_network                 │         OK │  0.002 seconds │
    │ minimega.create_mac_addresses   │         OK │  0.001 seconds │
    │ misc.print_schedule             │         OK │  0.038 seconds │
    │ minimega.resolve_vm_images      │         OK │  0.010 seconds │
    │ minimega.configure_ips          │         OK │  0.001 seconds │
    │ minimega.send_miniweb_arp       │         OK │  0.000 seconds │
    │ minimega.schedules_ready        │         OK │  0.000 seconds │
    │ vm_resource.schedule            │         OK │  0.031 seconds │
    │ vm_resource.validate            │         OK │  0.009 seconds │
    │ minimega.parse_experiment_graph │         OK │  2.984 seconds │
    │ minimega.launch                 │         OK │  0.000 seconds │
    ├─────────────────────────────────┼────────────┼────────────────┤
    │                                 │ Total Time │ 18.396 seconds │
    └─────────────────────────────────┴────────────┴────────────────┘
                Dependency resolution took 1.377 seconds

Notice that there is an additional model component (:ref:`minimega.create_mac_addresses_mc`) run between :ref:`control_network_mc` and :ref:`misc.print_schedule_mc`.
Therefore, when inspecting the schedule output it is important to be aware of the dependency graph ordering.

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
