# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-04-11 06:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('crm', '0023_user_field_is_mandatory'),
        ('market', '0009_DefaultBuyPriceIzZero'),
        ('timeline', '0012_ordering'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationsLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('send_date', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='crm.Customer')),
                ('sessions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='timeline.Entry')),
                ('subscriptions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='market.Subscription')),
            ],
        ),
    ]