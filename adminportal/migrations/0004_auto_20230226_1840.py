from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0003_initial'),
    ]

    operations = [
        UnaccentExtension()
    ]
