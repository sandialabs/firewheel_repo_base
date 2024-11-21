.. _misc.blank_graph_mc:

################
misc.blank_graph
################

This Model Component instantiates a new FIREWHEEL :py:class:`ExperimentGraph <firewheel.control.experiment_graph.ExperimentGraph>` and sets it to ``self.g``.
The creation of an experiment graph is necessary for users to decorate this graph with new VMs (i.e., :py:class:`Vertexes <firewheel.control.experiment_graph.Vertex`) and connections between them (i.e., :py:class:`Edges <firewheel.control.experiment_graph.Edge`).
See :ref:`experiment-graph` for more details on this import part of FIREWHEEL's architecture.
Due to the importance of this Model Component, all new topologies will likely depend on this MC likely by depending on the the MC attribute ``graph``.

**Attribute Provides:**
    * ``graph``

******
Plugin
******

.. automodule:: misc.blank_graph_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
