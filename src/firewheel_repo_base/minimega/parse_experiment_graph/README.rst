.. _minimega.parse_experiment_graph_mc:

###############################
minimega.parse_experiment_graph
###############################

This MC performs all of the heavy processing for parsing the experiment graph, converting it minimega commands (via `discovery <https://github.com/sandia-minimega/discovery/>`_), launching the experiment with `minimega <https://www.sandia.gov/minimega/>`_, and starting a :ref:`vm-resource-handler` for each VM.
Once this MC has finished processing the experiment has effectively been launched.

**Attribute Provides:**
    * ``minimega_parsed_experiment_graph``

**Attribute Depends:**
    * ``testbed_available``
    * ``mac_addresses``
    * ``ips``
    * ``vm_image_details``
    * ``topology``
    * ``validated_vm_resource_schedule_database``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`
    * :ref:`minimega.emulated_entities_mc`

******
Plugin
******

.. automodule:: minimega.parse_experiment_graph_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
