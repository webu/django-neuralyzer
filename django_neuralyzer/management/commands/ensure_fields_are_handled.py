import logging

from django.core.management.base import BaseCommand

from django_neuralyzer.base import BaseNeuralyzer
from django_neuralyzer.utils import get_app_submodules


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        # ensure neuralyzers has been loaded
        list(get_app_submodules("neuralyzers"))
        # get all subclasses
        anon_classes = all_subclasses(BaseNeuralyzer)
        errors = []

        for klass in anon_classes:
            model = klass.Meta.model
            anon_fields = klass()._get_class_attributes()
            for field in model._meta.fields:
                if field.name not in anon_fields:
                    errors.append(
                        f"Neuralyzer {klass.__name__} is missing field {field.name} for model {model.__name__}"
                    )
        if errors:
            logger.error("Following models have not been fully handled: \n" + "\n".join(errors))
