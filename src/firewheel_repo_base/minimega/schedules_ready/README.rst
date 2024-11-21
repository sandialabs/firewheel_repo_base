.. _minimega.schedules_ready_mc:

########################
minimega.schedules_ready
########################

This MC helps order the model component dependency graph by depending on various attributes which must occur before the VMR schedules can be complete.
Therefore, **ALL** VMRs should be scheduled before this MC is run.

**Attribute Provides:**
    * ``schedules_ready``

**Attribute Depends:**
    * ``topology``
    * ``ips``
    * ``vm_image_details``
    * ``sent_arp``
