import json
from pathlib import Path

import rich

from firewheel.control.experiment_graph import AbstractPlugin


class PrintSchedule(AbstractPlugin):
    """
    Print out all VM Resource Schedules in JSON format.
    This Plugin optionally takes in a filename which will be used to write output.
    If no filename is provided, the schedule will be printed to ``stdout``.
    """

    def _generate_schedule(self):
        """
        Get the ``vm_resource_schedule`` for all vertices in the graph and effectively
        print the schedule attributes.
        """

        full_schedule = {}
        for vert in self.g.get_vertices():
            vm_schedule = vert.__dict__.get("vm_resource_schedule", None)

            if vm_schedule is None:
                continue

            # Iterate over schedule
            for entry in vm_schedule.get_schedule():
                full_schedule[entry.start_time] = full_schedule.get(entry.start_time, [])
                full_schedule[entry.start_time].append({
                    "name": vert.name,
                    "executable": entry.executable,
                    "arguments": entry.arguments,
                    "data": entry.data,
                    "pause": entry.pause,
                })

        return dict(sorted(full_schedule.items()))

    def run(self, output_file=""):
        """
        Identifies whether the output should be printed or added to a file.
        If a output file is identified, the schedule output is produced in JSON format.

        Args:
            output_file (str, optional): The name/path to a file for the JSON output.
                Defaults to ``""``.
        """
        schedule = self._generate_schedule()
        if output_file:
            with open(output_file, "w", encoding="UTF-8") as out:
                json.dump(schedule, out)
            rich.print(
                "[b yellow]Output experiment schedule to: "
                f"[magenta]{Path(output_file).absolute()!s}"
            )
        else:
            rich.print(schedule)
