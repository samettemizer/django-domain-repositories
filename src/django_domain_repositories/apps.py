from django.apps import AppConfig


class DomainRepositoriesConfig(AppConfig):
    name = "django_domain_repositories"
    verbose_name = "Domain Repositories"

    def ready(self):
        from .registry import autodiscover_repositories

        autodiscover_repositories()
