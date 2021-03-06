# Generated by Django 4.0.5 on 2022-06-21 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Sync_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoySkladDBRetailDemand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(help_text='Остаток товара на складе')),
                ('demand_date', models.DateTimeField(blank=True, default=None, help_text='Дата продажи', null=True)),
                ('uuid', models.ForeignKey(db_column='uuid', help_text='Идентификатор проданного товара', on_delete=django.db.models.deletion.DO_NOTHING, to='Sync_app.moyskladdbgood')),
            ],
        ),
    ]
