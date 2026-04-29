from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0022_remove_meal_is_favorite_alter_entry_id_alter_food_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='meal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='meals.meal'),
        ),
        migrations.AddField(
            model_name='entry',
            name='food',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='meals.food'),
        ),
    ]
