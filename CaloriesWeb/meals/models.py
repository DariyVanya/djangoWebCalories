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


class MealVerification(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Чернетка'),
        ('pending', 'На перевірці'),
        ('approved', 'Схвалено'),
        ('rejected', 'Відхилено'),
        ('banned', 'Заблоковано'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_verifications')
    original_meal = models.ForeignKey('Meal', on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_requests')
    name = models.CharField(max_length=100)
    grams = models.PositiveIntegerField(default=100)
    recipe = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    image = models.ImageField(upload_to='meal_verifications/', null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_meals')
    review_comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Verification {self.name} ({self.get_status_display()})"


class MealVerificationProduct(models.Model):
    verification = models.ForeignKey(MealVerification, on_delete=models.CASCADE, related_name='products')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    grams = models.FloatField()

    def __str__(self):
        return f"{self.verification.name} - {self.food.name}"


class MealVerificationTag(models.Model):
    verification = models.ForeignKey(MealVerification, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.verification.name} - {self.tag.name}"


class MealComment(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.meal.name}"