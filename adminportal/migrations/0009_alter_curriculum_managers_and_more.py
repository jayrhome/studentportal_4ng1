# Generated by Django 4.1.2 on 2023-02-13 22:33

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0008_alter_shs_strand_definition_and_more'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='curriculum',
            managers=[
                ('allObjects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='sectionschedule',
            name='time_in',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='sectionschedule',
            name='time_out',
            field=models.TimeField(null=True),
        ),
    ]
