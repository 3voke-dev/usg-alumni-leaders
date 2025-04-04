# Generated by Django 5.1.7 on 2025-04-01 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_alter_candidate_photo_alter_election_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='photo',
            field=models.ImageField(blank=True, default='photos/default-candidate.jpg', null=True, upload_to='photos/'),
        ),
        migrations.AlterField(
            model_name='election',
            name='photo',
            field=models.ImageField(blank=True, default='photos/default-election.jpg', null=True, upload_to='photos/'),
        ),
    ]
