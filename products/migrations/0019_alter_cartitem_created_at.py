# Generated by Django 5.1.6 on 2025-03-01 12:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_alter_cartitem_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 1, 12, 48, 45, 881051, tzinfo=datetime.timezone.utc)),
        ),
    ]
