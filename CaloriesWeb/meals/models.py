from django.db import models
from django.contrib.auth.models import User

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
    grams = models.PositiveIntegerField(default=100)
    recipe = models.TextField(null=True)
    link = models.URLField(null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='meal_images/', null=True, blank=True)

class MealProducts(models.Model):
    meal = models.ForeignKey("Meal", on_delete=models.CASCADE)
    food = models.ForeignKey("Food", on_delete=models.CASCADE)
    grams = models.FloatField()

class Entry (models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    grams = models.FloatField(default=100)
    date = models.DateField(auto_now_add=True)

