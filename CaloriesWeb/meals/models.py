from django.db import models

class Food(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    grams = models.FloatField()
    calories = models.IntegerField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fats = models.FloatField()

class Meal(models.Model):
    name = models.CharField(max_length=100)
    grams = models.FloatField(default=100)
    recipe = models.TextField(null=True)
    link = models.URLField(null=True)

class MealProducts(models.Model):
    meal = models.ForeignKey("Meal", on_delete=models.CASCADE)
    food = models.ForeignKey("Food", on_delete=models.CASCADE)
    grams = models.FloatField()