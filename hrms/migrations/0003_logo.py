# Generated by Django 5.0 on 2024-01-29 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hrms', '0002_regularizationemp_hrs_worked'),
    ]

    operations = [
        migrations.CreateModel(
            name='Logo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.CharField(max_length=100)),
                ('logo_image', models.ImageField(blank=True, null=True, upload_to='logos/')),
            ],
            options={
                'verbose_name': 'Logo',
                'verbose_name_plural': 'Logos',
                'db_table': 'tbl_logo',
                'managed': True,
            },
        ),
    ]
