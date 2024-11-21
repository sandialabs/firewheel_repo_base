import warnings

from firewheel.control.experiment_graph import AbstractPlugin


class Plugin(AbstractPlugin):
    """Provide a deprecation warning for this MC."""

    def run(self):
        """Provide a deprecation warning for this MC."""
        warnings.simplefilter("always", DeprecationWarning)
        warnings.warn(
            "The Runner VM Resource is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=1,
        )
