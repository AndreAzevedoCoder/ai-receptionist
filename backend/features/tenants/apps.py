from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.features.tenants'
    verbose_name = 'Tenants'
