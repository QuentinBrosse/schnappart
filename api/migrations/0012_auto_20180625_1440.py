# Generated by Django 2.0.6 on 2018-06-25 14:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20180625_1429'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='searchresultfeature',
            unique_together={('search_result', 'feature')},
        ),
    ]
