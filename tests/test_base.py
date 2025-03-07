from django.db.models import Q
from django.test import TestCase

from django_neuralyzer.base import BaseNeuralyzer as BaseBaseNeuralyzer
from django_neuralyzer.base import lazy_attribute

from . import models


class BaseNeuralyzer(BaseBaseNeuralyzer):
    class Meta:
        pass

    def __init__(self):
        """
        The reason we set declarations manually in ``__init__`` is because we want to
        patch objects individually for unit testing purposes, without using the
        ``run()`` method. In general cases, declarations will be set by ``run()``
        """
        self._declarations = self.get_declarations()


class BaseTestCase(TestCase):
    def test_get_manager(self):
        class Neuralyzer(BaseNeuralyzer):
            class Meta:
                model = models.Person
                manager = models.PersonAnotherQuerySet

        neuralyzer = Neuralyzer()
        self.assertEqual(neuralyzer.get_manager(), models.PersonAnotherQuerySet)

    def test_get_queryset(self):
        sample_obj = models.person_factory()

        class Neuralyzer(BaseNeuralyzer):
            class Meta:
                model = models.Person

        neuralyzer = Neuralyzer()
        result = neuralyzer.get_queryset()
        self.assertSequenceEqual(result, [sample_obj])

    def test_patch_object(self):
        fake_first_name = "foo"

        class Neuralyzer(BaseNeuralyzer):
            first_name = fake_first_name
            last_name = fake_first_name
            raw_data = "{1: 2}"

        obj = models.person_factory(last_name="")  # empty data should be kept empty

        neuralyzer = Neuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.first_name, "foo")
        self.assertEqual(obj.last_name, "")
        self.assertEqual(obj.raw_data, "{1: 2}")

    def test_inheritance(self):
        class ParentNeuralyzer(BaseNeuralyzer):
            first_name = "parent"
            last_name = "parent"

        class ChildNeuralyzer(ParentNeuralyzer):
            last_name = "child"

        obj = models.person_factory()

        neuralyzer = ChildNeuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.first_name, "parent")
        self.assertEqual(obj.last_name, "child")

    def test_run(self):
        class Neuralyzer(BaseNeuralyzer):
            class Meta:
                model = models.Person

            first_name = "xyz"

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.run()

        obj.refresh_from_db()
        self.assertEqual(obj.first_name, "xyz")

    def test_run_without_fields(self):
        class Neuralyzer(BaseNeuralyzer):
            def clean(self, obj):
                obj.first_name = "xyz"
                obj.save()

            class Meta:
                model = models.Person

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.run()

        obj.refresh_from_db()
        self.assertEqual(obj.first_name, "xyz")

    def test_run_filters_dict(self):
        class Neuralyzer(BaseNeuralyzer):
            first_name = "xyz"

            class Meta:
                model = models.Person

        obja = models.person_factory()
        objb = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.run(filters={"pk": 1})

        obja.refresh_from_db()
        objb.refresh_from_db()
        self.assertEqual(obja.first_name, "xyz")
        self.assertEqual(objb.first_name, "A")

    def test_run_filters_Q(self):
        class Neuralyzer(BaseNeuralyzer):
            first_name = "xyz"

            class Meta:
                model = models.Person

        obja = models.person_factory()
        objb = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.run(filters=~Q(pk=1))

        obja.refresh_from_db()
        objb.refresh_from_db()
        self.assertEqual(obja.first_name, "A")
        self.assertEqual(objb.first_name, "xyz")

    def test_lazy_attribute(self):
        fake_first_name = lazy_attribute(lambda o: o.last_name)

        class Neuralyzer(BaseNeuralyzer):
            first_name = fake_first_name

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.first_name, obj.last_name)

    def test_lazy_attribute_decorator(self):
        class Neuralyzer(BaseNeuralyzer):
            @lazy_attribute
            def first_name(self):
                return "xyz"

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.first_name, "xyz")

    def test_raw_attributes(self):
        class Neuralyzer(BaseNeuralyzer):
            raw_data = "{}"

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.raw_data, "{}")

    def test_clean(self):
        class Neuralyzer(BaseNeuralyzer):
            line1 = ""
            line2 = ""
            line3 = ""

            def clean(self, obj):
                obj.line1 = "foo"
                obj.line2 = "bar"

        obj = models.person_factory()

        neuralyzer = Neuralyzer()
        neuralyzer.patch_object(obj)
        self.assertEqual(obj.line1, "foo")
        self.assertEqual(obj.line2, "bar")
        self.assertEqual(obj.line3, "")

    def test_get_declarations(self):
        # Ensure the order is preserved
        class Neuralyzer(BaseNeuralyzer):
            a = lazy_attribute(lambda o: 4)
            c = lazy_attribute(lambda o: 6)
            b = lazy_attribute(lambda o: 5)

            def get_queryset(self):
                return []

        neuralyzer = Neuralyzer()
        self.assertEqual(list(neuralyzer.get_declarations().keys()), ["a", "c", "b"])
