from firewheel.control.experiment_graph import AbstractPlugin, ExperimentGraph


class BlankGraph(AbstractPlugin):
    """Create the experiment graph for all future plugins."""

    def run(self):
        """
        Create a new instance of :py:class:`firewheel.control.experiment_graph.ExperimentGraph`
        and make it accessible by storing it in ``self.g``.
        """
        self.g = ExperimentGraph()
