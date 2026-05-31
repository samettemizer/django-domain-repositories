import importlib
import inspect
import os
import pkgutil

from .conf import get_domain_config, get_setting

# Global registry: contract class -> resolved concrete instance or class
_registry = {}
_singletons = {}

DOMAIN_DIRECTORIES = [
    "contracts",
    "enums",
    "events",
    "exceptions",
    "helpers",
    "jobs",
    "listeners",
    "models",
    "observers",
    "repositories",
    "services",
    "views",
]


def get_required_domain_directories():
    """Return the list of conventional sub-directories for a domain."""
    return list(DOMAIN_DIRECTORIES)


def ensure_domain_directories(domain_path):
    """Create all conventional sub-directories inside *domain_path*."""
    for directory in DOMAIN_DIRECTORIES:
        full_path = os.path.join(domain_path, directory)
        os.makedirs(full_path, exist_ok=True)


def autodiscover_repositories():
    """
    Scan every domain package under the configured ``DOMAINS_PACKAGE``,
    find repository contracts (abstract classes) and bind them to their
    concrete implementations based on the configured driver.

    Naming convention
    -----------------
    Contract module : ``<domains_pkg>.<domain>.contracts.<domain>_repository``
    Contract class  : ``<Domain>Repository``  (abstract)

    Concrete module : ``<domains_pkg>.<domain>.repositories.<domain>_<driver>``
    Concrete class  : ``<Domain><Driver>``
    """
    domains_package_path = get_setting("DOMAINS_PACKAGE")

    try:
        domains_pkg = importlib.import_module(domains_package_path)
    except ModuleNotFoundError:
        return

    pkg_path = getattr(domains_pkg, "__path__", None)
    if pkg_path is None:
        return

    for importer, domain_name, is_pkg in pkgutil.iter_modules(pkg_path):
        if not is_pkg:
            continue

        _register_domain(domains_package_path, domain_name)


def _register_domain(domains_package_path, domain_name):
    """Register a single domain's contract -> concrete binding."""
    cfg = get_domain_config(domain_name)
    driver = cfg["driver"]
    binding = cfg["binding"]

    _validate_binding(binding, domain_name)

    contract_class = _import_contract_class(domains_package_path, domain_name)
    if contract_class is None:
        return

    concrete_class = _import_concrete_class(
        domains_package_path, domain_name, driver
    )
    if concrete_class is None:
        return

    _apply_binding(binding, contract_class, concrete_class)


def _validate_binding(binding, domain_name):
    allowed = get_setting("BINDING_OPTIONS")
    if binding not in allowed:
        raise ValueError(
            f"Unsupported binding method '{binding}' for domain "
            f"'{domain_name}'. Allowed: {', '.join(allowed)}."
        )


def _import_contract_class(domains_package_path, domain_name):
    """
    Import and return the abstract contract class, or ``None`` if not found.

    The class must be abstract (i.e. defined with ``abc.ABC`` or
    ``abc.ABCMeta``); a concrete class in the contracts directory is
    silently skipped.

    Expected module : ``<domains_pkg>.<domain>.contracts.<domain>_repository``
    Expected class  : ``<Domain>Repository``
    """
    module_path = (
        f"{domains_package_path}.{domain_name}.contracts.{domain_name}_repository"
    )
    class_name = f"{_to_pascal(domain_name)}Repository"

    cls = _safe_import_class(module_path, class_name)

    if cls is None or not inspect.isabstract(cls):
        return None

    return cls


def _import_concrete_class(domains_package_path, domain_name, driver):
    """
    Import and return the concrete implementation class, or ``None``.

    The class must not be abstract; an abstract class in the repositories
    directory is silently skipped.

    Expected module : ``<domains_pkg>.<domain>.repositories.<domain>_<driver>``
    Expected class  : ``<Domain><Driver>``
    """
    module_path = (
        f"{domains_package_path}.{domain_name}.repositories."
        f"{domain_name}_{driver}"
    )
    class_name = f"{_to_pascal(domain_name)}{_to_pascal(driver)}"

    cls = _safe_import_class(module_path, class_name)

    if cls is None or inspect.isabstract(cls):
        return None

    return cls


def _safe_import_class(module_path, class_name):
    """Import *class_name* from *module_path*; return ``None`` on failure."""
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return None

    cls = getattr(module, class_name, None)
    if cls is None or not inspect.isclass(cls):
        return None

    return cls


def _apply_binding(binding, contract_class, concrete_class):
    """Store the contract -> concrete mapping in the global registry."""
    _registry[contract_class] = {
        "concrete": concrete_class,
        "binding": binding,
    }


def resolve(contract_class):
    """
    Resolve a contract to its concrete instance.

    * ``transient`` – a new instance is created on every call.
    * ``singleton`` – the same instance is reused.
    """
    entry = _registry.get(contract_class)
    if entry is None:
        raise LookupError(
            f"No concrete implementation registered for "
            f"'{contract_class.__module__}.{contract_class.__qualname__}'."
        )

    concrete_class = entry["concrete"]
    binding = entry["binding"]

    if binding == "singleton":
        if contract_class not in _singletons:
            _singletons[contract_class] = concrete_class()
        return _singletons[contract_class]

    return concrete_class()


def get_registry():
    """Return a shallow copy of the current registry (read-only helper)."""
    return dict(_registry)


def clear_registry():
    """Clear all bindings and cached singletons (useful for testing)."""
    _registry.clear()
    _singletons.clear()


def _to_pascal(snake_str):
    """Convert a ``snake_case`` or lowercase string to ``PascalCase``."""
    return "".join(part.capitalize() for part in snake_str.split("_"))