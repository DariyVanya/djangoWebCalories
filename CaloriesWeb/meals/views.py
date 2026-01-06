from django.shortcuts import render
from .models import Meal, MealProducts, Food

# Create your views here.
def meals(request):
    meals = Meal.objects.all()
    return render(request, "meals/meals.html", {"meals": meals})

def meal_detail(request, meal_id):
    meal = Meal.objects.get(id=meal_id)

    cpfc = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fats": 0
    }
    meal_products = MealProducts.objects.filter(meal_id=meal_id)

    grams = meal.grams
    if request.method == "POST":
        grams = int(request.POST.get("grams", meal.grams))


    for mp in meal_products:
        food = Food.objects.get(id=mp.food_id)
        cpfc["calories"] += food.calories / food.grams * mp.grams
        cpfc["protein"] += food.protein / food.grams * mp.grams
        cpfc["carbs"] += food.carbs / food.grams * mp.grams
        cpfc["fats"] += food.fats / food.grams * mp.grams

    cpfc["calories"] = round(cpfc["calories"]/meal.grams*grams)
    cpfc["protein"] = round(cpfc["protein"]/meal.grams*grams)
    cpfc["carbs"] = round(cpfc["carbs"]/meal.grams*grams)
    cpfc["fats"] = round(cpfc["fats"]/meal.grams*grams)

    data = {
        "meal": meal,
        "cpfc": cpfc,
        "grams": grams,
    }

    return render(request, "meals/mealItemDetailed.html", data)

def search(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        meals = Meal.objects.filter(name__icontains=query) if query else []
        return render(request, "meals/searchResults.html", {"meals": meals, "query": query})
