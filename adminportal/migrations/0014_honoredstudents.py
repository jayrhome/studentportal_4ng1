# Generated by Django 4.1.2 on 2023-02-06 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registrarportal', '0002_alter_schoolyear_options'),
        ('adminportal', '0013_delete_honoredstudents'),
    ]

    operations = [
        migrations.CreateModel(
            name='honoredStudents',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('honor', models.CharField(choices=[('h', 'With Honor'), ('hh', 'With High Honor'), ('hsh', 'With Highest Honor')], max_length=3, null=True)),
                ('gradPic', models.ImageField(default='graduationPictures/default.jpg', upload_to='graduationPictures/%Y')),
                ('date_created', models.DateTimeField(auto_now=True)),
                ('last_modified', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sy_graduated', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='graduateStudent', to='registrarportal.schoolyear')),
            ],
            options={
                'ordering': ['-date_created', 'name'],
            },
        ),
    ]