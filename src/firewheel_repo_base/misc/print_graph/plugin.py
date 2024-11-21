import inspect
from pathlib import Path

import rich
import networkx as nx

from firewheel.control.experiment_graph import AbstractPlugin


class PrintGraph(AbstractPlugin):
    """
    Print out the :py:class:`ExperimentGraph <firewheel.control.experiment_graph.ExperimentGraph>`
    in an easy-to-read text format. This Plugin optionally takes in a filename which will
    be used to write output. If no filename is provided, the graph will be printed
    to ``stdout`` using :py:func:`networkx.readwrite.text.write_network_text`.
    """

    def _generate_nx_graph(self):
        """
        Generate a NetworkX graph which contains a subset of critical attributes
        of each Vertex in the :py:class:`firewheel.control.experiment_graph.ExperimentGraph`.

        Each :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` should contain the
        following:

            * Basic node information - Name, Graph ID, etc.
            * All the classes which decorated that
              :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
            * Any "important" :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
              attributes (e.g. in ``{"vm", "vm_resource_schedule",
              "host", "type", "interfaces"}``).

        Each :py:class:`Edge <firewheel.control.experiment_graph.Edge>` should contain
        the following:

            * The source and destination
              :py:class:`Vertexes <firewheel.control.experiment_graph.Vertex>`
            * All the classes which decorated that
              :py:class:`Edge <firewheel.control.experiment_graph.Edge>`.
            * Any "important" :py:class:`Edge <firewheel.control.experiment_graph.Edge>`
              attributes (e.g. in ``{"dst_ip", "dst_network", "qos"}``).
            * The network information.

        Returns:
            networkx.Graph: The properly formatted text representation of the
                :py:class:`ExperimentGraph <firewheel.control.experiment_graph.ExperimentGraph>`.
        """

        print_graph = nx.Graph()
        for v in self.g.get_vertices():
            # Get decorators
            dec_names = ", ".join([str(dec.__name__) for dec in v.decorators])

            # Get attributes
            attributes = []
            for attr in v.__dict__.keys():
                if inspect.isroutine(v.__dict__[attr]):
                    continue
                attributes.append(attr)

            attrs = {}
            for attribute in attributes:
                if str(attribute) not in {
                    "vm",
                    "vm_resource_schedule",
                    "host",
                    "type",
                    "nx_data",
                    "interfaces",
                }:
                    continue
                attrs[str(attribute)] = str(v.__dict__[attribute])

            node_char = {}
            if v.type == "switch":
                node_char["viz"] = {
                    "color": {"a": 0.5, "r": 255, "g": 255, "b": 0},
                    "shape": "triangle",
                }
            if v.type == "host":
                node_char["viz"] = {
                    "color": {"a": 0.5, "r": 255, "g": 0, "b": 255},
                    "shape": "square",
                }
            if v.type == "router":
                node_char["viz"] = {
                    "color": {"a": 0.5, "r": 0, "g": 255, "b": 255},
                    "shape": "disc",
                }

            print_graph.add_node(
                v.name,
                graph_id=v.graph_id,
                decorated_by=dec_names,
                **attrs,
                **node_char,
            )

        for edge in self.g.get_edges():
            # Get attributes
            attributes = []
            for attr in edge.__dict__.keys():
                if inspect.isroutine(edge.__dict__[attr]):
                    continue
                attributes.append(attr)

            attrs = {}
            for attribute in attributes:
                if str(attribute) not in {"dst_ip", "dst_network", "qos"}:
                    continue
                attrs[str(attribute)] = str(edge.__dict__[attribute])

            print_graph.add_edge(
                edge.source["object"].name,
                edge.destination["object"].name,
                decorated_by=", ".join([str(dec.__name__) for dec in edge.decorators]),
                **attrs,
            )

        return print_graph

    def _generate_text(self):
        """
        Generate a text representation of every vertex in the ExperimentGraph.
        The text representation should contain the following sections:

            * *NODE* - The :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects
              ``graph_id``.
            * *DECORATED BY* - All the classes which decorated that
              :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
            * *NEIGHBORS* - All neighbors (connected
              :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects).
            * *ATTRIBUTES* - Any :py:class:`Vertexes <firewheel.control.experiment_graph.Vertex>`
              attributes.
            * *METHODS* - All :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects
              methods.

        Returns:
            str: The properly formatted text representation of the
                :py:class:`ExperimentGraph <firewheel.control.experiment_graph.ExperimentGraph>`.
        """
        text = ""

        for v in self.g.get_vertices():
            text += f"NODE {v.graph_id!s}\n"

            dec_names = [str(dec.__name__) for dec in v.decorators]
            dec_names.sort()
            text += f"  DECORATED BY: {' '.join(dec_names)}\n"

            text += "  NEIGHBORS:\n"
            for neighbor in v.get_neighbors():
                text += f"    {neighbor.graph_id!s}\n"

            attributes = []
            methods = []

            for attr in v.__dict__.keys():
                if inspect.isroutine(v.__dict__[attr]):
                    methods.append(attr)
                else:
                    attributes.append(attr)

            text += "  ATTRIBUTES:\n"
            for attribute in attributes:
                attr_str = str(v.__dict__[attribute])
                attr_split = attr_str.strip().split("\n")
                if len(attr_split) > 1:
                    attr_str = "\n"
                    for line in attr_split:
                        attr_str += f"      {line.strip()}\n"
                text += f"    {attribute!s}: {attr_str.strip()}\n"

            text += "  METHODS:\n"
            for method in methods:
                text += f"    {method!s}\n"

        return text

    def run(self, output_file=""):
        """
        Identifies whether the output should be printed or added to a file.
        The file extension determines whether or not it should be output as a
        text file or a `GEXF <http://gexf.net>`_
        file which can be read by graph visualization tools, such as
        `Gephi <https://gephi.org/>`_.

        Args:
            output_file (str, optional): The name/path to a file for the text output.
                If the extension is ``.gexf``, than the file will use the GEXF file format.
                Otherwise will use text format. Defaults to ``""``.
        """
        if Path(output_file).suffix.lower() == ".gexf":
            nx.write_gexf(self._generate_nx_graph(), output_file)
        elif output_file:
            rich.print(
                "[b yellow]Unknown [cyan]print_graph[/cyan] file extension provided, "
                "defaulting to creating a text-representation in file: "
                f"[magenta]{Path(output_file).absolute()!s}"
            )
            with open(output_file, "w", encoding="UTF-8") as out:
                out.write(self._generate_text())
        else:
            nx.write_network_text(self._generate_nx_graph(), rich.print, end="")
