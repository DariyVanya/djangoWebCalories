from django.shortcuts import render, redirect
from meals.models import Meal, Food, MealProducts
from meals.models import Entry 
from datetime import date

# Create your views here.
def today(request):

    if request.user.is_authenticated:
        entries = Entry.objects.filter(
            user=request.user,
            date=date.today()
        ).select_related('meal')


        calories_total = 0
        protein_total = 0
        carbs_total = 0
        fats_total = 0

        for entry in entries:
            meal = Meal.objects.get(id=entry.meal.id)
            for food in MealProducts.objects.filter(meal_id=meal.id):
                food_item = Food.objects.get(id=food.food_id)
                calories_total += food_item.calories / food_item.grams * food.grams
                protein_total += food_item.protein / food_item.grams * food.grams
                carbs_total += food_item.carbs / food_item.grams * food.grams
                fats_total += food_item.fats / food_item.grams * food.grams

        cpfc = {
            'calories': round(calories_total),
            'protein': round(protein_total),
            'carbs': round(carbs_total),
            'fats': round(fats_total)
        }
    else:
        entries = []
        cpfc = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
    

    data = {
        'entries': entries,
        'cpfc': cpfc
    }
    print("CPFC:", cpfc)

    return render(request, "today/today.html", data)

def add_meal_today(request):
    query = request.GET.get("q", "")
    meals = Meal.objects.none()

    if query:
        meals = Meal.objects.filter(name__icontains=query)

    if request.method == "POST":
        meal_id = request.POST["meal_id"]
        grams = request.POST["grams"]

        Entry.objects.create(
            user=request.user,
            meal_id=meal_id,
            grams=grams,
            date=date.today()
        )
        return redirect("today")

    return render(request, "today/addMealToday.html", {
        "meals": meals,
        "query": query
    })
