from django.conf import settings

DEFAULTS = {
    # Default repository implementation driver suffix.
    # Contract : domains/<domain>/contracts/<domain>_repository.py
    # Concrete : domains/<domain>/repositories/<domain>_<driver>.py
    #
    # Example with default driver "django_orm" (Django's built-in ORM):
    #   FooRepository => FooDjangoOrm
    #
    # Use any custom driver string to point to an alternative backend,
    # e.g. "sqlalchemy", "mongo", "memory".
    "DEFAULT_DRIVER": "django_orm",

    # Allowed binding strategies.
    "BINDING_OPTIONS": ["transient", "singleton"],

    # Default binding strategy applied when no domain override is set.
    # "transient" returns a new instance on every resolve call.
    # "singleton" returns the same instance throughout the request lifecycle.
    "DEFAULT_BINDING": "transient",

    # Domain-specific overrides.
    #
    # Example:
    # "DOMAINS": {
    #     "foo": {
    #         "driver": "django_orm",
    #         "binding": "transient",
    #     },
    #     "bar": {
    #         "driver": "sqlalchemy",
    #         "binding": "singleton",
    #     },
    # }
    "DOMAINS": {},

    # Base Python package path where domain directories reside.
    # Typically something like "myproject.domains" or "domains".
    "DOMAINS_PACKAGE": "domains",
}


def get_setting(name):
    """
    Return a single configuration value from the user's
    ``DOMAIN_REPOSITORIES`` dict in ``settings.py``, falling back to the
    package default when the key is not overridden.
    """
    user_settings = getattr(settings, "DOMAIN_REPOSITORIES", {})
    return user_settings.get(name, DEFAULTS[name])


def get_domain_config(domain_name):
    """
    Return the merged configuration dict for a specific domain.
    Domain-level keys (``driver``, ``binding``) override the global defaults.
    """
    domains = get_setting("DOMAINS")
    domain_cfg = domains.get(domain_name, {})

    return {
        "driver": domain_cfg.get("driver", get_setting("DEFAULT_DRIVER")),
        "binding": domain_cfg.get("binding", get_setting("DEFAULT_BINDING")),
    }
