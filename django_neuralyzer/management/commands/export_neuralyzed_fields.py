import csv
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
    help = "Export all neuralyzed fields with their neuralized value"

    def handle(self, *args, **options):
        # ensure neuralyzers has been loaded
        list(get_app_submodules("neuralyzers"))
        # get all subclasses
        anon_classes = all_subclasses(BaseNeuralyzer)
        # errors = []
        data = {}

        for klass in anon_classes:
            model = klass.Meta.model
            neuralyzer = klass()
            anon_fields = neuralyzer._get_class_attributes()
            noop_fields = neuralyzer._excluded_attributes
            model_fields = model._meta.fields
            # model_fields_names = [field.name for field in model_fields]
            data[klass] = []
            for field in model_fields:
                if isinstance(field, (ManyToManyField, OneToOneField)):
                    continue

                if field.name not in anon_fields and field.name not in noop_fields:
                    data[klass].append(
                        {"field": field, "neuralyzed_to": "__NOT_NEURALYZED__", "dynamic": "?"}
                    )
                    continue

                neuralyzed_op = getattr(neuralyzer, field.name)
                if callable(neuralyzed_op):
                    neuralyzed_data = neuralyzed_op.__doc__ or "__UNDOCUMENTED__"
                    dynamic = True
                elif neuralyzed_op in ["", [], {}, None]:
                    neuralyzed_data = "__EMPTY__"
                    dynamic = False
                else:
                    neuralyzed_data = neuralyzed_op
                    dynamic = False
                data[klass].append(
                    {"field": field, "neuralyzed_to": neuralyzed_data, "dynamic": dynamic}
                )

        self.to_csv(data)

    def to_csv(self, data):
        fieldnames = [
            "model",
            "field_name",
            "verbose_name",
            "help_text",
            "neuralyzed_to",
            "dynamic",
        ]
        with open("neuralyzer_export.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for neuralyzer, fields in data.items():
                for field in fields:
                    writer.writerow(
                        dict(
                            model=neuralyzer.Meta.model._meta.verbose_name,
                            field_name=field["field"].name,
                            verbose_name=field["field"].verbose_name,
                            help_text=field["field"].help_text,
                            neuralyzed_to=field["neuralyzed_to"],
                            dynamic=field["dynamic"],
                        )
                    )
