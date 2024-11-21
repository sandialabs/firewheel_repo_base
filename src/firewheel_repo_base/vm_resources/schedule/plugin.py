import pickle

from base_objects import VMEndpoint

from firewheel.control.experiment_graph import AbstractPlugin
from firewheel.vm_resource_manager.vm_mapping import VMMapping
from firewheel.vm_resource_manager.schedule_db import ScheduleDb


class UploadSchedule(AbstractPlugin):
    """
    This plugin accomplishes three primary objectives:
        1. Upload all VM schedules to the
           :py:class:`ScheduleDb <firewheel.vm_resource_manager.schedule_db.ScheduleDb>`.
        2. Upload the VM mapping to the
           :py:class:`VMMapping <firewheel.vm_resource_manager.vm_mapping.VMMapping>` database.
        3. Identify all VMRs for an experiment.
    """

    def _put_all_vm_resource_schedules(self):
        """
        For every :py:class:`VMEndpoint <base_objects.VMEndpoint>` in the experiment,
        iterate over its schedule and put it in the schedule database.
        """
        sched_db = ScheduleDb()
        vm_mapping = VMMapping()
        sched_list = []
        mapping_list = []
        for vert in self.g.get_vertices():
            if not vert.is_decorated_by(VMEndpoint):
                continue
            try:
                control_ip = None
                try:
                    control_ip = str(vert.control_ip)
                except AttributeError:
                    pass
                sched = list(vert.vm_resource_schedule.get_schedule())
                self.log.debug("Schedule length %d for %s", len(sched), vert.name)
                schedule = pickle.dumps(sched)

                # add required vm_resources to set
                for item in sched:
                    for data_entry in item.data:
                        try:
                            self.g.required_vm_resources.add(data_entry["filename"])
                        except KeyError:
                            # some vm_resources don't have files to upload
                            continue

                self.log.debug("Got schedule %s for %s", schedule, vert.name)
                sched_list.append(
                    {"server_name": vert.name, "text": schedule, "ip": control_ip}
                )
                self.log.debug(
                    "Adding %s %s %s to VM Mapping", vert.uuid, control_ip, vert.name
                )
                mapping_list.append(
                    {
                        "server_uuid": vert.uuid,
                        "server_name": vert.name,
                        "control_ip": control_ip,
                    }
                )
            except AttributeError:
                self.log.exception('No vm_resource schedule for VM "%s".', vert.name)

        # Batch insert into the databases for performance reasons
        if sched_list:
            sched_db.batch_put(sched_list)
            vm_mapping.batch_put(mapping_list)
        else:
            self.log.warning("No vm resources scheduled")

    def run(self):
        """
        Initialize the required VMR set and call
        :py:meth:`vm_resource.schedule._put_all_vm_resource_schedules`
        which contains the main Plugin logic.
        """
        self.g.required_vm_resources = set()
        self._put_all_vm_resource_schedules()
