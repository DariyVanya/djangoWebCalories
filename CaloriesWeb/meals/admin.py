from django.contrib import admin
from .models import Food, Meal, MealTag, FoodTag, Tag, MealFavorites

admin.site.register(Food)
admin.site.register(Meal)
admin.site.register(MealTag)
admin.site.register(FoodTag)
admin.site.register(Tag)
admin.site.register(MealFavorites)
