# Generated by Django 4.0.3 on 2022-11-05 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studentportal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_password_changed_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
