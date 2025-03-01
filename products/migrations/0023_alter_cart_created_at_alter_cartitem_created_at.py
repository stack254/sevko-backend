# Generated by Django 5.1.6 on 2025-03-01 13:38

import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_alter_cartitem_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 1, 13, 37, 56, 463422, tzinfo=datetime.timezone.utc)),
        ),
    ]
