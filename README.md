# django-domain-repositories

Automatic repository discovery and container binding for domain-driven Django applications.

This package eliminates manual wiring of repository contracts to their implementations. It scans your configured domains package on startup, applies a strict naming convention, and registers everything automatically — no decorators, no explicit registration calls.

## Installation

```bash
pip install django-domain-repositories
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_domain_repositories",
]
```

## Naming Convention

| Role | Pattern |
|------|---------|
| Contract module | `<domains_pkg>.<domain>.contracts.<domain>_repository` |
| Contract class | `<Domain>Repository` (abstract) |
| Concrete module | `<domains_pkg>.<domain>.repositories.<domain>_<driver>` |
| Concrete class | `<Domain><Driver>` |

**Example with `foo` domain and default `django_orm` driver:**

```
myproject/domains/foo/contracts/foo_repository.py   → class FooRepository (ABC)
myproject/domains/foo/repositories/foo_django_orm.py → class FooDjangoOrm(FooRepository)
```

If a contract or concrete class does not exist for a domain, that domain is silently skipped.

## Domain Structure

```
myproject/
  domains/
    __init__.py
    foo/
      __init__.py
      contracts/
        foo_repository.py
      repositories/
        foo_django_orm.py
      models/
      services/
    bar/
      __init__.py
      contracts/
        bar_repository.py
      repositories/
        bar_sqlalchemy.py
```

## Configuration

```python
# settings.py

DOMAIN_REPOSITORIES = {
    "DEFAULT_DRIVER": "django_orm",        # default driver suffix
    "DEFAULT_BINDING": "transient",        # new instance per resolve call
    "BINDING_OPTIONS": ["transient", "singleton"],
    "DOMAINS_PACKAGE": "myproject.domains",

    # Per-domain overrides
    "DOMAINS": {
        "foo": {"driver": "django_orm", "binding": "transient"},
        "bar": {"driver": "sqlalchemy", "binding": "singleton"},
    },
}
```

`transient` returns a new instance on every `resolve()` call. `singleton` returns the same instance throughout the process lifetime.

## Resolving a Repository

```python
from django_domain_repositories import resolve
from myproject.domains.foo.contracts.foo_repository import FooRepository

repo = resolve(FooRepository)
```

## Directory Scaffolding

```python
from django_domain_repositories import ensure_domain_directories

ensure_domain_directories("/path/to/myproject/domains/foo")
```

Creates the conventional subdirectories: `contracts`, `repositories`, `models`, `services`, `enums`, `events`, `exceptions`, `helpers`, `jobs`, `listeners`, `observers`, `views`.

## Testing

```python
from django_domain_repositories.registry import clear_registry, _registry

def test_something():
    clear_registry()
    # register a fake manually, test, then clear again
```

## Out of Scope

This package handles repository registration only. Signals, middleware, and other domain concerns are intentionally left out.

## License

MIT
