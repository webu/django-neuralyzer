import logging

from django.core.management.base import BaseCommand
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.related import OneToOneField

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
            print(f"Neuralyzer: {klass}")
            model = klass.Meta.model
            anon_fields = klass()._get_class_attributes()
            model_fields = model._meta.fields
            model_fields_names = [field.name for field in model_fields]
            for field in model_fields:
                if isinstance(field, (ManyToManyField, OneToOneField)):
                    continue

                if field.name not in anon_fields:
                    errors.append(
                        f"Neuralyzer {klass.__name__} is missing field {field.name} for model {model.__name__}"
                    )
            for field in anon_fields:
                if field not in model_fields_names:
                    errors.append(
                        f"Neuralyzer {klass.__name__} has extra field {field} for model {model.__name__}"
                    )

        if errors:
            logger.error("Following models have not been fully handled: \n" + "\n".join(errors))
        else:
            print("All models neuralyzed include all fields!")
