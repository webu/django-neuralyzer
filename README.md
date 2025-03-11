# Django Neuralyzer

[![PyPi - version](https://img.shields.io/pypi/v/django-neuralyzer.svg?style=flat-square)](https://pypi.python.org/pypi/django-neuralyzer)
[![Licence](https://img.shields.io/pypi/l/django-neuralyzer.svg?style=flat-square)](https://pypi.python.org/pypi/django-neuralyzer)
[![Python version](https://img.shields.io/pypi/pyversions/django-neuralyzer.svg?style=flat-square)](https://pypi.python.org/pypi/django-neuralyzer)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json&style=flat-square)](https://github.com/charliermarsh/ruff)

Anonymize instance data according to your need (GDPR, used in not-so-safe environments... )

<p align="center">
<img src="https://github.com/webu/django-neuralyzer/blob/main/zebu-in-black.png"/>
</p>


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

Lazy attributes can be defined as inline lambdas or methods, as shown below, using the `lazy_attribute` function/decorator.

```py
from django_neuralyzer.base import BaseNeuralyzer, lazy_attribute

from your_app.models import Person

class PersonNeuralyzer(BaseNeuralyzer):
   name = lazy_attribute(lambda o: 'x' * len(o.name))

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

If you want to ensure a field is handled, but you don't want to change its value, you can set it to `NEURALYZER_NOOP`:

```py
from django_neuralyzer.base import BaseNeuralyzer, NEURALYZER_NOOP

from your_app.models import Person

class PersonNeuralyzer(BaseNeuralyzer):
   id = NEURALYZER_NOOP
   name = lazy_attribute(lambda o: 'x' * len(o.name))

   class Meta:
      model = Person
```

this way, `ensure_fields_are_handled` will not complain that `id` is not handled.

## Why neuralyzer ?

In [Men in Black](https://meninblack.fandom.com/wiki/Neuralyzer), a "neuralyzer" is a tool that wipe the mind of anybody who sees the flash via isolating and editing certain element of their memory.

This is exactly what this django package intent to do (remove or fake some attributes of instances), so we find it funny to name it like that.
