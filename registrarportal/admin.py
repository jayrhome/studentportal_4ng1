from django.contrib import admin
from django.apps import apps

for each_model in apps.get_app_config('registrarportal').models.values():
    admin.site.register(each_model)
