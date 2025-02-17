# Django anonymizable

Anonymize instance data according to your need (GDPR, used in not-so-safe environments... )

**Heavily inspired by [django-anon](https://github.com/Tesorio/django-anon/)**

Like django-anon, django-anonymizable will help you anonymize your model instance so it can be shared among developers, helping to reproduce bugs and make performance improvements in a production-like environment.
It also provide ability to target specific instance and not the whole database at once, so it can be use for GDPR compliance or "forget about be" feature of your app.

## Usage

Use `django-anonymizable.BaseAnonymizer` to define your anonymizer classes:

```py
import anon

from your_app.models import Person

class PersonAnonymizer(anon.BaseAnonymizer):
   email = anon.fake_email

   # You can use static values instead of callables
   is_admin = False

   class Meta:
      model = Person

# run anonymizer: be cautious, this will affect your current database!
person = Person.objects.last()
# anonymize full table:
PersonAnonymizer().run()
# anonymize only some instance
PersonAnonymizer().run(pks=[person.pk])
```

### Lazy attributes

Lazy attributes can be defined as inline lambdas or methods, as shown below, using the `django_anonymizable.lazy_attribute` function/decorator.

```py
import django_anonymizable

from your_app.models import Person

class PersonAnonymizer(django_anonymizable.BaseAnonymizer):
   name = anon.lazy_attribute(lambda o: 'x' * len(o.name))

   @lazy_attribute
   def date_of_birth(self):
      # keep year and month
      return self.date_of_birth.replace(day=1)

   class Meta:
      model = Person
```

## Management command

Ensure that all field of your model are anonymizable:

1. add `django_anonymizable` at the end of your `INSTALLED_APPS`
2. load your anonymizers class in your app ready:
3. run the `ensure_fields_are_anonymizable` command

```py
class MyAppConfig(AppConfig):
    ...

    def ready(self) -> None:
        ...
        # load anonymizers so managements command know that there is some subclasses of BaseAnonymizer
        from myapp.anonymizers import *  # noqa

        return super().ready()
```

```shell
django-manage ensure_fields_are_anonymizable
```
