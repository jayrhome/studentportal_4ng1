# Generated by Django 4.1.2 on 2023-02-13 23:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrarportal', '0001_initial'),
        ('adminportal', '0009_alter_curriculum_managers_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='schoolsections',
            unique_together={('sy', 'name')},
        ),
    ]
