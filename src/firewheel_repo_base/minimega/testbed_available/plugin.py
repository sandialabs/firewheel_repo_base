import firewheel.vm_resource_manager.api as vrm_api
from firewheel.lib.minimega.api import minimegaAPI
from firewheel.control.experiment_graph import AbstractPlugin


class ExistingExperimentError(Exception):
    """
    This exception is thrown when the :ref:`minimega.testbed_available_mc` plugin detects that
    an experiment is running, but a user has requested to launch another experiment.
    It provides a helpful error message to the user indicating how to clear the testbed.
    """

    def __init__(self, msg=None):
        """
        Initialize the Exception and create a descriptive error message.

        Args:
            msg (str, optional): Add a message for the user. Defaults to :py:data:`None`.
        """
        Exception.__init__(self)
        self.msg = msg
        if self.msg is None:
            self.msg = (
                "There is already a FIREWHEEL experiment running. To reset"
                " the testbed use the command: 'firewheel restart'."
            )
        else:
            self.msg = msg

    def __str__(self):
        """
        Return the message.

        Returns:
            str: The message for the user.
        """
        return self.msg


class Plugin(AbstractPlugin):
    """
    This plugin is responsible for carrying out the main
    functionality of this model component (i.e. identifying whether a current experiment
    is running).
    """

    def run(self):
        """
        This run method checks to see if any VMs exist in minimega and throws an exception
        if they do. Additionally, it will ensure that the experiment launch time is not set.
        If it is, then we assume an experiment is running and throw an error.
        If it is not set, then we can set the launch time.

        Raises:
            ExistingExperimentError: If an existing experiment is running.
        """
        mm_api = minimegaAPI()
        if mm_api.mm_vms():
            raise ExistingExperimentError

        if vrm_api.get_experiment_launch_time() is not None:
            raise ExistingExperimentError

        vrm_api.set_experiment_launch_time()
