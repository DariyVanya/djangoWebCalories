from django.shortcuts import render
from .models import Meal

# Create your views here.
def meals(request):
    meals = Meal.objects.all()
    return render(request, "meals/meals.html", {"meals": meals})

def meal_detail(request, meal_id):
    meal = Meal.objects.get(id=meal_id)
    return render(request, "meals/mealItemDetailed.html", {"meal": meal})