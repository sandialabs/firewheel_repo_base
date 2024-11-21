from base_objects import VMEndpoint
from vyos.helium118 import Helium118
from linux.ubuntu1604 import Ubuntu1604Server
from minimega.emulated_entities import MinimegaEmulatedVM

from firewheel.control.image_store import ImageStore
from firewheel.control.experiment_graph import AbstractPlugin


class ResolveVMImages(AbstractPlugin):
    """
    Assign a default image to all :py:class:`VMEndpoints <base_objects.VMEndpoint>`.
    """

    default_images = {
        "host": Ubuntu1604Server,
        "router": Helium118,
        "switch": Ubuntu1604Server,
    }

    def _assign_default_images(self):
        """
        For every :py:class:`VMEndpoint <base_objects.VMEndpoint>` in the experiment graph,
        assign an image if one hasn't been assigned already. If a type is not specified for an
        endpoint, use ``"host"``. Default images are specified based on the type property.
        """
        for v in self.g.get_vertices():
            if v.is_decorated_by(VMEndpoint):
                v.vm["image_store"] = {
                    "path": self.image_store.cache,
                    "name": self.image_store.store,
                }
                has_image = False
                try:
                    image_name = v.vm["image"]
                    if image_name:
                        has_image = True
                except AttributeError:
                    self.log.debug('Assigning default image to VM "%s".', v.name)
                except KeyError:
                    has_image = False

                if not has_image:
                    # Assign a default image.
                    try:
                        # Based on v.type
                        v.decorate(self.default_images[v.type])
                    except AttributeError:
                        # We have no type. Just make a default host.
                        # We already know this is a VMEndpoint.
                        v.decorate(self.default_images["host"])
                    except KeyError:
                        # Unknown type.
                        self.log.warning(
                            'Encountered unknown type for VM "%s". Cannot assign a default image.',
                            v.name,
                        )
                        continue
                # We currently only handle minimega VMs.
                v.decorate(MinimegaEmulatedVM)

    def run(self):
        """
        Create the :py:class:`ImageStore <firewheel.control.image_store.ImageStore>`
        and call :py:meth:`_assign_default_images` which performs the main plugin logic.
        """
        self.image_store = ImageStore()
        self._assign_default_images()
