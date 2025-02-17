import logging

from django.core.management.base import BaseCommand

from django_anonymizable.base import BaseAnonymizer


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        anon_classes = all_subclasses(BaseAnonymizer)
        errors = []

        for klass in anon_classes:
            model = klass.Meta.model
            anon_fields = klass()._get_class_attributes()
            for field in model._meta.fields:
                if field.name not in anon_fields:
                    errors.append(f"Field {field} is not anonymizable for model {model}")
        if errors:
            raise ValueError("\n".join(errors))
