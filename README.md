# Django Neuralyzer

Anonymize instance data according to your need (GDPR, used in not-so-safe environments... )

**Heavily inspired by [django-anon](https://github.com/Tesorio/django-anon/)**

Like `django-anon`, `django-neuralyzer` will help you anonymize your model instance so it can be shared among developers, helping to reproduce bugs and make performance improvements in a production-like environment.

It also provide ability to target specific instance and not the whole database at once, so it can be use for GDPR compliance or "forget about be" feature of your app.

## Usage

Use `django-neuralyzer.BaseNeuralyzer` to define your neuralyzer classes:

```py
from django_neuralyzer.base import BaseNeuralyzer

from your_app.models import Person

class PersonNeuralyzer(BaseNeuralyzer):
   email = "example@anonymized.org"

   # You can use static values instead of callables
   is_admin = False

   class Meta:
      model = Person

# run neuralyzer: be cautious, this will affect your current database!
person = Person.objects.last()
# neuralyze full table:
PersonNeuralyzer().run()
# neuralyze only some instance
PersonNeuralyzer().run(filters={"pk": person.pk})
```

### Lazy attributes

Lazy attributes can be defined as inline lambdas or methods, as shown below, using the `django_neuralyzer.lazy_attribute` function/decorator.

```py
from django_neuralyzer import BaseNeuralyzer

from your_app.models import Person

class PersonNeuralyzer(BaseNeuralyzer):
   name = anon.lazy_attribute(lambda o: 'x' * len(o.name))

   @lazy_attribute
   def date_of_birth(self):
      # keep year and month
      return self.date_of_birth.replace(day=1)

   class Meta:
      model = Person
```

## Management command

Ensure that all field of your model are handle by the neuralyzer:

1. add `django_neuralyzer` at the end of your `INSTALLED_APPS`
2. run the `ensure_fields_are_handled` command

```shell
django-manage ensure_fields_are_handled
```

## Why neuralyzer ?

In [Men in Black](https://meninblack.fandom.com/wiki/Neuralyzer), a "neuralyzer" is a tool that wipe the mind of anybody who sees the flash via isolating and editing certain element of their memory.

This is exactly what this django package intent to do (remove or fake some attributes of instances), so we find it funny to name it like that.
