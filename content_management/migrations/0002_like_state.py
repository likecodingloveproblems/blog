# Generated by Django 4.2.13 on 2024-05-18 00:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='like',
            name='state',
            field=models.IntegerField(choices=[(1, 'Ok'), (2, 'Rate Limited')], default=1, verbose_name='state'),
        ),
    ]
