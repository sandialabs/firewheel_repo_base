.. _minimega.launch_mc:

###############
minimega.launch
###############

This MC primarily is responsible for creating the MC dependency tree which results in starting an emulation-based experiment via `minimega <https://www.sandia.gov/minimega/>`_.
By using this MC, users can successfully launch their experiments.
For example, the following command will launch the :ref:`tests.router_tree_mc`::

    firewheel experiment tests.router_tree:1 minimega.launch

This MC primarily relies on :ref:`minimega.parse_experiment_graph_mc` to help generate the necessary dependency graph.

**Attribute Depends:**
    * ``minimega_parsed_experiment_graph``
