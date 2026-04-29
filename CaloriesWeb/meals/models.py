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

    def __str__(self):
        return self.name
    

class Meal(models.Model):
    name = models.CharField(max_length=100)
    grams = models.PositiveIntegerField(default=100)
    recipe = models.TextField(null=True)
    link = models.URLField(null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(default='fallback.png', null=True, blank=True)
    popularity = models.IntegerField()

    def __str__(self):
        return self.name

class MealFavorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    

class MealProducts(models.Model):
    meal = models.ForeignKey("Meal", on_delete=models.CASCADE)
    food = models.ForeignKey("Food", on_delete=models.CASCADE)
    grams = models.FloatField()

    def __str__(self):
        return self.meal.name + " " + self.food.name

class Entry (models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, null=True, blank=True)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
    grams = models.FloatField(default=100)
    date = models.DateField(auto_now_add=True)

class MealTag(models.Model):
    meal = models.ForeignKey("Meal", on_delete=models.CASCADE)
    tag = models.ForeignKey("Tag", on_delete=models.CASCADE)

    def __str__(self):
        return self.meal.name + " " + self.tag.name

class FoodTag(models.Model):
    food = models.ForeignKey("Food", on_delete=models.CASCADE)
    tag = models.ForeignKey("Tag", on_delete=models.CASCADE)

    def __str__(self):
        return self.food.name + " " + self.tag.name
    

class Tag(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name