# Generated by Django 4.1.2 on 2022-12-05 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0003_alter_student_admission_details_elem_clc_address_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='sample_mods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('date_created', models.DateTimeField(auto_now=True)),
                ('last_modified', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]