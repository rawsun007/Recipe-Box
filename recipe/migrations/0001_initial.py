# Generated by Django 5.0.4 on 2024-11-18 11:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=100)),
                ('about', models.TextField(max_length=200)),
                ('img', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SavedRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_label', models.CharField(max_length=500)),
                ('recipe_url', models.URLField(max_length=2000)),
                ('recipe_image', models.URLField(blank=True, null=True)),
                ('meal_type', models.CharField(blank=True, max_length=1000, null=True)),
                ('cuisine_type', models.CharField(blank=True, max_length=1000, null=True)),
                ('dish_type', models.CharField(blank=True, max_length=1000, null=True)),
                ('source', models.CharField(blank=True, max_length=1000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_recipes', models.ManyToManyField(related_name='saved_by', to='recipe.savedrecipe')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
