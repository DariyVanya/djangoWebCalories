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


def _entry_calories(entry, meal_products_map):
    if entry.meal_id:
        meal = entry.meal
        portion_factor = entry.grams / meal.grams if meal.grams > 0 else 1
        total = 0.0
        for item in meal_products_map.get(meal.id, []):
            food_item = item.food
            if food_item.grams > 0:
                total += food_item.calories / food_item.grams * item.grams * portion_factor
        return total

    if entry.food_id:
        food_item = entry.food
        if food_item.grams > 0:
            portion_factor = entry.grams / food_item.grams
            return food_item.calories * portion_factor

    return 0.0


def _build_meal_products_map(entries):
    meal_ids = {entry.meal_id for entry in entries if entry.meal_id}
    if not meal_ids:
        return {}

    products = MealProducts.objects.filter(meal_id__in=meal_ids).select_related("food")
    meal_products_map = {}
    for item in products:
        meal_products_map.setdefault(item.meal_id, []).append(item)
    return meal_products_map


def _shift_month(base_date, delta):
    year_offset, month_index = divmod(base_date.month - 1 + delta, 12)
    return date(base_date.year + year_offset, month_index + 1, 1)


def _recommended_macros(details):
    if not details:
        return None

    goal_calories = getattr(details, "goal_calories", 0) or 0
    weight_kg = getattr(details, "weight_kg", 0) or 0

    if goal_calories <= 0 or weight_kg <= 0:
        return None

    plan = getattr(details, "calorie_plan", "maintain")
    if plan == "cut":
        protein_per_kg = 2.0
        fat_per_kg = 0.8
    elif plan == "bulk":
        protein_per_kg = 1.8
        fat_per_kg = 1.0
    else:
        protein_per_kg = 1.6
        fat_per_kg = 0.9

    protein_g = weight_kg * protein_per_kg
    fat_g = weight_kg * fat_per_kg
    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9

    if protein_kcal + fat_kcal > goal_calories:
        total = protein_kcal + fat_kcal
        scale = goal_calories / total if total else 0
        protein_g *= scale
        fat_g *= scale
        carbs_g = 0
    else:
        carbs_kcal = goal_calories - protein_kcal - fat_kcal
        carbs_g = carbs_kcal / 4

    return {
        "protein": round(protein_g),
        "fats": round(fat_g),
        "carbs": round(carbs_g),
        "calories": round(goal_calories),
    }


def today(request):
    today_date = date.today()
    yesterday_date = today_date - timedelta(days=1)
    tab = request.GET.get("tab", "today")
    history_period = request.GET.get("period", "week")

    if request.user.is_authenticated:
        entries = Entry.objects.filter(
            user=request.user,
            date=today_date
        ).select_related('meal', 'food')

        goal_calories = request.user.details.goal_calories
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

        macro_recommendations = _recommended_macros(request.user.details)
        macro_progress = None
        macro_warning_items = []
        macro_warning_threshold = 120
        if macro_recommendations:
            def _pct(value, target):
                if target and target > 0:
                    return min(round((value / target) * 100), 100)
                return 0

            def _raw_pct(value, target):
                if target and target > 0:
                    return round((value / target) * 100)
                return 0

            macro_progress = {
                "calories": _pct(cpfc["calories"], macro_recommendations["calories"]),
                "protein": _pct(cpfc["protein"], macro_recommendations["protein"]),
                "carbs": _pct(cpfc["carbs"], macro_recommendations["carbs"]),
                "fats": _pct(cpfc["fats"], macro_recommendations["fats"]),
            }

            macro_labels = {
                "protein": "Білки",
                "carbs": "Вуглеводи",
                "fats": "Жири",
            }
            for key, label in macro_labels.items():
                pct = _raw_pct(cpfc[key], macro_recommendations[key])
                if pct >= macro_warning_threshold:
                    macro_warning_items.append({
                        "label": label,
                        "value": cpfc[key],
                        "target": macro_recommendations[key],
                        "pct": pct,
                    })

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

        history_items = []
        history_label = ""
        history_stats = {
            "total": 0,
            "average": 0,
            "max": 0,
            "min": 0,
            "days": 0,
        }
        chart_items = []
        if history_period not in ("week", "month", "year"):
            history_period = "week"

        if history_period == "year":
            current_month = today_date.replace(day=1)
            start_month = _shift_month(current_month, -11)
            history_start = start_month
            history_entries = Entry.objects.filter(
                user=request.user,
                date__range=(history_start, today_date),
            ).select_related('meal', 'food')

            meal_products_map = _build_meal_products_map(history_entries)
            month_totals = {}
            for entry in history_entries:
                key = (entry.date.year, entry.date.month)
                month_totals[key] = month_totals.get(key, 0.0) + _entry_calories(entry, meal_products_map)

            month_cursor = start_month
            while month_cursor <= current_month:
                key = (month_cursor.year, month_cursor.month)
                history_items.append({
                    "label": f"{month_cursor.month:02d}.{month_cursor.year}",
                    "calories": round(month_totals.get(key, 0.0)),
                })
                month_cursor = _shift_month(month_cursor, 1)

            history_label = "Останні 12 місяців"
        else:
            days_back = 6 if history_period == "week" else 29
            history_start = today_date - timedelta(days=days_back)
            history_entries = Entry.objects.filter(
                user=request.user,
                date__range=(history_start, today_date),
            ).select_related('meal', 'food')

            meal_products_map = _build_meal_products_map(history_entries)
            daily_totals = {history_start + timedelta(days=offset): 0.0 for offset in range(days_back + 1)}
            for entry in history_entries:
                daily_totals[entry.date] = daily_totals.get(entry.date, 0.0) + _entry_calories(entry, meal_products_map)

            for day in sorted(daily_totals.keys()):
                history_items.append({
                    "label": day.strftime("%d.%m"),
                    "calories": round(daily_totals[day]),
                })

            history_label = "Останні 7 днів" if history_period == "week" else "Останні 30 днів"

        if history_items:
            calories_values = [item["calories"] for item in history_items]
            total_calories = sum(calories_values)
            days_count = len(calories_values)
            max_calories = max(calories_values)
            min_calories = min(calories_values)
            average_calories = round(total_calories / days_count) if days_count else 0

            history_stats = {
                "total": round(total_calories),
                "average": average_calories,
                "max": max_calories,
                "min": min_calories,
                "days": days_count,
            }

            chart_scale = max(max_calories, 1)
            for item in history_items:
                pct = round((item["calories"] / chart_scale) * 100)
                chart_items.append({
                    "label": item["label"],
                    "calories": item["calories"],
                    "pct": pct,
                })
    else:
        entries = []
        goal_calories = 0
        cpfc = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
        cut_min_calories = 0
        is_over_goal = False
        macro_recommendations = None
        macro_progress = None
        macro_warning_items = []
        macro_warning_threshold = 120
        history_items = []
        history_label = ""
        history_stats = {
            "total": 0,
            "average": 0,
            "max": 0,
            "min": 0,
            "days": 0,
        }
        chart_items = []
    

    data = {
        'entries': entries,
        'cpfc': cpfc,
        'goal_calories': goal_calories,
        'cut_min_calories': cut_min_calories,
        'is_over_goal': is_over_goal,
        'calorie_plan': request.user.details.calorie_plan if request.user.is_authenticated else None,
        'streak_info': streak_info if request.user.is_authenticated else None,
        'today_date': today_date,
        'yesterday_date': yesterday_date,
        'tab': tab,
        'history_period': history_period,
        'history_items': history_items,
        'history_label': history_label,
        'history_stats': history_stats,
        'chart_items': chart_items,
        'macro_recommendations': macro_recommendations,
        'macro_progress': macro_progress,
        'macro_warning_items': macro_warning_items,
        'macro_warning_threshold': macro_warning_threshold,
        'calorie_plan_display': request.user.details.get_calorie_plan_display() if request.user.is_authenticated else None,
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
