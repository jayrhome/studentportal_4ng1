# Generated by Django 4.1.2 on 2023-02-12 18:16

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0002_initial'),
    ]

    operations = [
        UnaccentExtension()
    ]