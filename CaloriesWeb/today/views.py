from django.shortcuts import render, redirect, get_object_or_404
from meals.models import Meal, Food, MealProducts
from meals.models import Entry
from datetime import date, timedelta


def check_streak(user_details, cpfc):

    if user_details.date_last_streak_entry == date.today() - timedelta(days=2):
        user_details.current_streak = 0
        user_details.date_last_streak_entry = None

    if user_details.calorie_plan == 'cut':
        cut_min_calories = max(user_details.goal_calories - 300, 0)
        streak_reached = cut_min_calories <= cpfc['calories'] <= user_details.goal_calories
    else:
        streak_reached = cpfc['calories'] >= user_details.goal_calories

    if streak_reached:
        today = date.today()
        if user_details.current_streak > user_details.max_streak:
                user_details.max_streak = user_details.current_streak

        if user_details.date_last_streak_entry == today - timedelta(days=1):
            user_details.current_streak += 1
        elif user_details.date_last_streak_entry != today:
            user_details.current_streak = 1

        user_details.date_last_streak_entry = today
    elif not streak_reached and user_details.date_last_streak_entry == date.today():
        if user_details.current_streak != 0:
            if user_details.current_streak == user_details.max_streak:
                user_details.max_streak -= 1
            user_details.current_streak -= 1
            user_details.date_last_streak_entry = date.today() - timedelta(days=1)
        else:
            user_details.current_streak = 0
            user_details.date_last_streak_entry = None

# Create your views here.
def today(request):

    if request.user.is_authenticated:
        entries = Entry.objects.filter(
            user=request.user,
            date=date.today()
        ).select_related('meal', 'food')

        goal_calories = request.user.details.goal_calories
        today_date = date.today()
        yesterday_date = today_date - timedelta(days=1)

        calories_total = 0
        protein_total = 0
        carbs_total = 0
        fats_total = 0

        for entry in entries:
            if entry.meal_id:
                meal = entry.meal
                for food in MealProducts.objects.filter(meal_id=meal.id):
                    food_item = Food.objects.get(id=food.food_id)
                    # Scale nutrients from recipe proportion (meal.grams) to actual portion (entry.grams)
                    portion_factor = entry.grams / meal.grams if meal.grams > 0 else 1
                    calories_total += food_item.calories / food_item.grams * food.grams * portion_factor
                    protein_total += food_item.protein / food_item.grams * food.grams * portion_factor
                    carbs_total += food_item.carbs / food_item.grams * food.grams * portion_factor
                    fats_total += food_item.fats / food_item.grams * food.grams * portion_factor
            elif entry.food_id:
                food_item = entry.food
                if food_item.grams > 0:
                    portion_factor = entry.grams / food_item.grams
                    calories_total += food_item.calories * portion_factor
                    protein_total += food_item.protein * portion_factor
                    carbs_total += food_item.carbs * portion_factor
                    fats_total += food_item.fats * portion_factor

        cpfc = {
            'calories': round(calories_total),
            'protein': round(protein_total),
            'carbs': round(carbs_total),
            'fats': round(fats_total)
        }

        cut_min_calories = max(request.user.details.goal_calories - 300, 0)
        is_cut_plan = request.user.details.calorie_plan == 'cut'
        is_over_goal = is_cut_plan and cpfc['calories'] > request.user.details.goal_calories

        check_streak(request.user.details, cpfc)
        request.user.details.save()

        streak_info = {
            'current_streak': request.user.details.current_streak,
            'max_streak': request.user.details.max_streak,
            'date_last_streak_entry': request.user.details.date_last_streak_entry,
        }
    else:
        entries = []
        goal_calories = 0
        cpfc = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
        cut_min_calories = 0
        is_over_goal = False
    

    data = {
        'entries': entries,
        'cpfc': cpfc,
        'goal_calories': goal_calories,
        'cut_min_calories': cut_min_calories,
        'is_over_goal': is_over_goal,
        'calorie_plan': request.user.details.calorie_plan if request.user.is_authenticated else None,
        'streak_info': streak_info if request.user.is_authenticated else None,
        'today_date': today_date if request.user.is_authenticated else date.today(),
        'yesterday_date': yesterday_date if request.user.is_authenticated else date.today() - timedelta(days=1),
    }

    return render(request, "today/today.html", data)

def add_meal_today(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    raw_query = request.GET.get("q", "")
    query = raw_query.strip()
    meals = Meal.objects.none()
    foods = Food.objects.none()

    if query:
        query_folded = query.casefold()
        meals = [meal for meal in Meal.objects.all() if query_folded in meal.name.casefold()]
        foods = [food for food in Food.objects.all() if query_folded in food.name.casefold()]

    if request.method == "POST":
        entry_type = request.POST.get("entry_type")
        grams = request.POST.get("grams")

        if entry_type == "meal":
            meal_id = request.POST.get("meal_id")
            if meal_id and grams:
                Entry.objects.create(
                    user=request.user,
                    meal_id=meal_id,
                    grams=grams,
                    date=date.today()
                )
        elif entry_type == "food":
            food_id = request.POST.get("food_id")
            if food_id and grams:
                Entry.objects.create(
                    user=request.user,
                    food_id=food_id,
                    grams=grams,
                    date=date.today()
                )

        return redirect("today:today")

    return render(request, "today/addMealToday.html", {
        "meals": meals,
        "foods": foods,
        "query": raw_query
    })

def delete_today_entry(request, entry_id):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    entry = get_object_or_404(Entry, id=entry_id, user=request.user, date=date.today())
    if request.method == "POST":
        entry.delete()
    return redirect("today:today")
