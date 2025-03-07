from collections import OrderedDict
import inspect
from logging import getLogger

from django.db.models import Q

from .utils import import_from_path

logger = getLogger(__name__)


class OrderedDeclaration(object):
    """Any classes inheriting from this will have an unique global counter
    associated with it. This counter is used to determine the order in
    which fields were declarated

    Idea taken from: https://stackoverflow.com/a/4460034/639465
    Also inspired by https://github.com/FactoryBoy/factory_boy
    """

    global_counter = 0

    def __init__(self):
        self._order = self.__class__.global_counter
        self.__class__.global_counter += 1


class LazyAttribute(OrderedDeclaration):
    def __init__(self, lazy_fn):
        super(LazyAttribute, self).__init__()
        self.lazy_fn = lazy_fn

    def __call__(self, *args, **kwargs):
        return self.lazy_fn(*args, **kwargs)


def lazy_attribute(lazy_fn):
    """Returns LazyAttribute objects, that basically marks functions that
    should take `obj` as first parameter. This is useful when you need
    to take in consideration other values of `obj`

    Example:

    >>> full_name = lazy_attribute(o: o.first_name + o.last_name)

    """
    return LazyAttribute(lazy_fn)


class BaseNeuralyzer(object):
    def run(self, filters=None, select_chunk_size=None, **bulk_update_kwargs):
        self._declarations = self.get_declarations()

        queryset = self.get_queryset(filters=filters)
        update_fields = list(self._declarations.keys())

        # info used in log messages
        model_name = self.Meta.model.__name__

        logger.info("Updating {}...".format(model_name))

        manager = self.get_manager()
        objs = []
        for obj in queryset:
            self.patch_object(obj)
            objs.append(obj)

        if update_fields:
            manager.bulk_update(
                objs,
                update_fields,
                **dict(**bulk_update_kwargs),
            )
        else:
            logger.info("Skiping bulk update for {}... No fields to update".format(model_name))

        # Cascade to one to one relation
        if hasattr(self.Meta, "onetoone"):
            for relation, class_import in self.Meta.onetoone.items():
                neuralyzer = import_from_path(class_import)
                for obj in objs:
                    related_model = getattr(obj, relation)
                    if related_model:
                        neuralyzer().run(filters={"pk": related_model.pk})

    def get_manager(self):
        meta = self.Meta
        return getattr(meta, "manager", meta.model.objects)

    def get_queryset(self, filters=None):
        """Override this if you want to delimit the objects that should be
        affected by anonymization

        Args:
          filters: Q object or dict
        """
        qs = self.get_manager().all()
        if isinstance(filters, dict):
            qs = qs.filter(**filters)
        elif isinstance(filters, Q):
            qs = qs.filter(filters)
        return qs

    def patch_object(self, obj):
        """Update object attributes with fake data provided by replacers"""
        fields = [field for field in self._declarations if getattr(obj, field)]

        for field in fields:
            replacer = self._declarations[field]
            if isinstance(replacer, LazyAttribute):
                # Pass in obj for LazyAttributes
                new_value = replacer(obj)
            elif callable(replacer):
                new_value = replacer()
            else:
                new_value = replacer

            setattr(obj, field, new_value)

        self.clean(obj)

    def clean(self, obj):
        """Use this function if you need to update additional data that may
        rely on multiple fields, or if you need to update multiple fields
        at once
        """
        pass

    def get_declarations(self):
        """Returns ordered declarations. Any non-ordered declarations, for
        example any types that does not inherit from OrderedDeclaration
        will come first, as they are considered "raw" values and should
        not be affected by the order of other non-ordered declarations
        """

        def _sort_declaration(declaration):
            name, value = declaration
            if isinstance(value, OrderedDeclaration):
                return value._order
            else:
                # Any non-ordered declarations come first
                return -1

        declarations = self._get_class_attributes().items()
        sorted_declarations = sorted(declarations, key=_sort_declaration)

        return OrderedDict(sorted_declarations)

    @property
    def _excluded_attributes(self):
        meta = self.Meta
        return getattr(meta, "noop", [])

    def _get_class_attributes(self):
        """Return list of class attributes, which also includes methods and
        subclasses, ignoring any magic methods and reserved attributes
        as well as defined noop attributes
        """
        reserved_names = list(BaseNeuralyzer.__dict__.keys()) + ["Meta", "_declarations"]

        return {
            name: getattr(self, name)
            for name, value in inspect.getmembers_static(self)
            if not name.startswith("__")
            and name not in reserved_names
            and name not in self._excluded_attributes
        }

    class Meta:
        noop = []
        onetoone = {}
