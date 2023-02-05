from django.contrib.postgres.operations import UnaccentExtension

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0009_alter_school_events_options'),
    ]

    operations = [
        UnaccentExtension()
    ]
