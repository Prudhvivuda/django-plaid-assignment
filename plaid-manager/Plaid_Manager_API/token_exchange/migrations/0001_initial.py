# Generated by Django 3.2.6 on 2022-02-26 19:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.CharField(max_length=100)),
                ('balance_available', models.FloatField(default=None, null=True)),
                ('balance_current', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='APILogModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(max_length=200, unique=True)),
                ('api_type', models.CharField(max_length=200)),
                ('date_log', models.DateTimeField(auto_now_add=True, verbose_name='date_log')),
            ],
        ),
        migrations.CreateModel(
            name='TransactionModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100)),
                ('amount', models.FloatField()),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=100)),
                ('pending', models.BooleanField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='token_exchange.accountmodel')),
            ],
        ),
        migrations.CreateModel(
            name='BankItemModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_item_id', models.CharField(max_length=300, unique=True)),
                ('access_token', models.CharField(max_length=300, unique=True)),
                ('request_id', models.CharField(max_length=200)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='accountmodel',
            name='bank_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='token_exchange.bankitemmodel'),
        ),
    ]