from firewheel.control.experiment_graph import AbstractPlugin
from firewheel.control.model_component_exceptions import MissingRequiredVMResourcesError
from firewheel.vm_resource_manager.vm_resource_store import VmResourceStore


class ValidateVMResources(AbstractPlugin):
    """
    This Plugin ensures that all VMRs which have been scheduled have been uploaded to the
    :py:class:`firewheel.vm_resource_manager.vm_resource_store.VmResourceStore`.
    """

    def run(self):
        """
        Verify that every required VM resource has been uploaded.

        Raises:
            MissingRequiredVMResourcesError: Raised if any VMRs are missing.
        """
        missing_vm_resources = []
        vm_resource_store = VmResourceStore()
        for vm_resource in self.g.required_vm_resources:
            try:
                local_path = vm_resource_store.get_path(vm_resource)
                if not local_path:
                    self.log.error(
                        "Unable to get file: %s. Will try again just-in-time.",
                        vm_resource,
                    )
            except FileNotFoundError:
                missing_vm_resources.append(vm_resource)
                self.log.exception(
                    "Unable to get file: %s. There are typically a few reasons for this issue:\n"
                    "\t1. The VM resource isn't included in the MANIFEST file.\n"
                    "\t2. The VM resource is contained in a Model Component which is"
                    "not part of the experiment.\n"
                    "\t3. A misspelled VM resource file name.",
                    vm_resource,
                )
        if missing_vm_resources:
            raise MissingRequiredVMResourcesError(missing_vm_resources)
