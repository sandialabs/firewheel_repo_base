from generic_vm_objects import GenericRouter

from firewheel.control.experiment_graph import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    This MC helps verify that there are no collisions between Autonomous System (AS)
    numbers in a given experiment. If there is a collision, a :py:exc:`RuntimeError` is thrown.
    """

    def run(self):
        """
        Perform the main logic for the AS checking MC.

        Raises:
            RuntimeError: If two routers have the same AS number.
        """
        as_dict = {}
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(GenericRouter):
                as_num = int(vertex.get_bgp_as())
                # `get_bgp_as` will return a negative number if the AS doesn't exist
                if as_num < 0:
                    continue
                if as_num in as_dict:
                    raise RuntimeError(
                        "Two different routers have the same AS number, this can cause"
                        " strange routing issues within your topology. Please"
                        " fix this prior to launching your experiment."
                        f" Routers: {as_dict[as_num]} and {vertex.name} share the"
                        f" AS number: {as_num}."
                    )
                as_dict[as_num] = vertex.name
