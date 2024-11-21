"""This module contains all necessary Model Component Objects for misc.networkx."""

from base_objects import FalseEdge

from firewheel.control.experiment_graph import Edge, Vertex, require_class


@require_class(FalseEdge)
class NxEdge:
    """This class is intended to indicate that an
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>` is a NetworkX
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>` in the graph.
    That is, the :py:class:`Edge <firewheel.control.experiment_graph.Edge>`
    exists in the graph but won't be used when the graph is instantiated.
    This is useful when generating graphs using NetworkX.
    """

    def __init__(self):
        """Creates ``self.is_nx`` and sets it to :py:data:`True`."""
        self.is_nx = True


def convert_nx_to_fw(nx_graph, fw_graph):
    """
    This function enables converting a NetworkX :py:class:`networkx.Graph` to a
    :py:class:`firewheel.control.experiment_graph.ExperimentGraph`. Specifically,
    nodes in the NetworkX :py:class:`networkx.Graph` are converted to
    :py:class:`Vertecies <firewheel.control.experiment_graph.Vertex>` and the
    edges are converted to :py:class:`NxEdge`. The attribute dictionary for both
    NetworkX nodes/edges are preserved in a new attribute on the
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` and
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>` called ``nx_data``.

    Args:
        nx_graph (networkx.Graph): The :py:class:`networkx.Graph` to convert.
        fw_graph (ExperimentGraph): The FIREWHEEL
            :py:class:`firewheel.control.experiment_graph.ExperimentGraph` where
            the new nodes/edges will be added.
    """
    for node, data in nx_graph.nodes(data=True):
        fw_node = Vertex(fw_graph, name=node, graph_id=node)
        fw_node.nx_data = data

    for src, dst, data in nx_graph.edges(data=True):
        edge = Edge(fw_graph.find_vertex_by_id(src), fw_graph.find_vertex_by_id(dst))
        edge.decorate(NxEdge)
        edge.nx_data = data
