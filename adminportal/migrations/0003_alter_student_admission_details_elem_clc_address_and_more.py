# Generated by Django 4.1.2 on 2022-12-03 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminportal', '0002_auto_20221202_0009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student_admission_details',
            name='elem_clc_address',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='student_admission_details',
            name='elem_community_learning_center',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='student_admission_details',
            name='jhs_clc_address',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='student_admission_details',
            name='jhs_community_learning_center',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]