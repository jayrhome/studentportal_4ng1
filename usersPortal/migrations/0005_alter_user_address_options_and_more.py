# Generated by Django 4.1.2 on 2023-01-27 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usersPortal', '0004_alter_user_address_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user_address',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterModelOptions(
            name='user_contactnumber',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterModelOptions(
            name='user_photo',
            options={'ordering': ['-date_created']},
        ),
    ]