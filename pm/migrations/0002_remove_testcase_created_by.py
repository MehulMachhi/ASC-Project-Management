# Generated by Django 5.1.7 on 2025-04-02 07:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testcase',
            name='created_by',
        ),
    ]
