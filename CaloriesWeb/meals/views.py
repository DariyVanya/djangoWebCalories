from django.shortcuts import render, redirect, get_object_or_404
from .models import Meal, MealProducts, Food, MealFavorites, Tag, MealTag
import datetime
from datetime import timedelta
from collections import defaultdict

# Create your views here.
def meals(request):
    meals = Meal.objects.all().order_by("name")
    can_create_meal = False
    open_groups = [group_name for group_name in request.GET.getlist("open_group") if group_name]
    panel_open = request.GET.get("filter_open") == "1"
    favourites_only = request.GET.get("favourites") == "1"

    selected_tag_ids = []
    raw_tag_ids = request.GET.getlist("tag")
    for tag_id in raw_tag_ids:
        if str(tag_id).isdigit():
            selected_tag_ids.append(int(tag_id))

    if selected_tag_ids:
        meals = meals.filter(mealtag__tag_id__in=selected_tag_ids).distinct()

    if favourites_only:
        if request.user.is_authenticated:
            meals = meals.filter(mealfavorites__user=request.user).distinct()
        else:
            meals = meals.none()

    available_tags = Tag.objects.all().order_by("type", "name")
    selected_tag_ids_set = set(selected_tag_ids)
    grouped_tags = []
    for tag in available_tags:
        group_name = (tag.type or "Інше").strip() if tag.type else "Інше"
        is_selected = tag.id in selected_tag_ids_set

        if grouped_tags and grouped_tags[-1]["type"] == group_name:
            grouped_tags[-1]["tags"].append(tag)
            if is_selected:
                grouped_tags[-1]["has_selected"] = True
        else:
            grouped_tags.append({
                "type": group_name,
                "tags": [tag],
                "has_selected": is_selected,
            })

    if request.user.is_authenticated:
        user_details = getattr(request.user, "details", None)
        if user_details:
            can_create_meal = user_details.current_streak >= 30
    
    favourite_meals = set()
    if request.user.is_authenticated:
        favourite_meals = set(MealFavorites.objects.filter(user=request.user).values_list("meal_id", flat=True))
    

    data = {
        "meals": meals,
        "can_create_meal": can_create_meal,
        "favourite_meals": favourite_meals,
        "grouped_tags": grouped_tags,
        "selected_tag_ids": selected_tag_ids,
        "favourites_only": favourites_only,
        "open_groups": open_groups,
        "yesterday_date": datetime.date.today() - timedelta(days=1),
        "user_details": user_details if request.user.is_authenticated else None,
        "panel_open": panel_open or bool(selected_tag_ids) or bool(open_groups) or favourites_only,
    }

    return render(request, "meals/meals.html", data)

def meal_detail(request, meal_id):
    meal = get_object_or_404(Meal, id=meal_id)
    all_tags = Tag.objects.order_by("type", "name")
    meal_tag_ids = set(MealTag.objects.filter(meal=meal).values_list("tag_id", flat=True))
    grouped_tags_for_edit = []
    for tag in all_tags:
        group_name = (tag.type or "Інше").strip() if tag.type else "Інше"
        if grouped_tags_for_edit and grouped_tags_for_edit[-1]["type"] == group_name:
            grouped_tags_for_edit[-1]["tags"].append(tag)
        else:
            grouped_tags_for_edit.append({
                "type": group_name,
                "tags": [tag],
            })

    if request.method == "POST" and request.POST.get("action") == "update_meal":
        if request.user.is_authenticated and request.user == meal.author:
            name = (request.POST.get("name") or "").strip()
            grams = request.POST.get("grams")
            recipe = (request.POST.get("recipe") or "").strip()
            link = (request.POST.get("link") or "").strip()
            image = request.FILES.get("image")
            selected_tag_ids = []
            for raw_id in request.POST.getlist("tag"):
                if str(raw_id).isdigit():
                    selected_tag_ids.append(int(raw_id))
            selected_tag_ids = list(set(selected_tag_ids))

            if name:
                meal.name = name
            if grams:
                meal.grams = grams

            meal.recipe = recipe or None
            meal.link = link or None

            if image:
                meal.image = image

            meal.save()

            MealTag.objects.filter(meal=meal).delete()
            selected_tags = Tag.objects.filter(id__in=selected_tag_ids)
            MealTag.objects.bulk_create([
                MealTag(meal=meal, tag=tag)
                for tag in selected_tags
            ])

        return redirect("meals:meal_detail", meal_id=meal.id)

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
        "is_favorite": request.user.is_authenticated and MealFavorites.objects.filter(user=request.user, meal=meal).exists(),
        "meal_tags": Tag.objects.filter(mealtag__meal=meal).order_by("type", "name"),
        "grouped_tags_for_edit": grouped_tags_for_edit,
        "meal_tag_ids": meal_tag_ids,
    }

    return render(request, "meals/mealItemDetailed.html", data)

def search(request):
    if request.method == "GET":
        raw_query = request.GET.get('q', '')
        query = raw_query.strip()
        query_folded = query.casefold()
        if query_folded:
            meals = [meal for meal in Meal.objects.all() if query_folded in meal.name.casefold()]
        else:
            meals = []
        return render(request, "meals/searchResults.html", {"meals": meals, "query": raw_query})

def add_meal(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    user_details = getattr(request.user, "details", None)
    if not user_details or user_details.current_streak < 30:
        return redirect("meals:meals")

    all_tags = Tag.objects.order_by("type", "name")
    grouped_tags = []
    for tag in all_tags:
        group_name = (tag.type or "Інше").strip() if tag.type else "Інше"
        if grouped_tags and grouped_tags[-1]["type"] == group_name:
            grouped_tags[-1]["tags"].append(tag)
        else:
            grouped_tags.append({
                "type": group_name,
                "tags": [tag],
            })
    selected_tag_ids = []

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        grams = request.POST.get("grams")
        recipe = (request.POST.get("recipe") or "").strip()
        link = (request.POST.get("link") or "").strip()
        image = request.FILES.get("image")
        for raw_id in request.POST.getlist("tag"):
            if str(raw_id).isdigit():
                selected_tag_ids.append(int(raw_id))
        selected_tag_ids = list(set(selected_tag_ids))

        if name and grams:
            meal = Meal(
                name=name,
                grams=grams,
                recipe=recipe or None,
                link=link or None,
                author=request.user,
                popularity=0,
            )
            if image:
                meal.image = image
            meal.save()

            selected_tags = Tag.objects.filter(id__in=selected_tag_ids)
            MealTag.objects.bulk_create([
                MealTag(meal=meal, tag=tag)
                for tag in selected_tags
            ])

            return redirect(f"{request.path}addfood/?meal_id={meal.id}")

    return render(request, "meals/addMeal.html", {
        "grouped_tags": grouped_tags,
        "selected_tag_ids": selected_tag_ids,
    })

def add_food_to_meal(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    meal_id = request.POST.get("meal_id") or request.GET.get("meal_id")
    if not meal_id:
        return redirect("meals:add_meal")

    meal = get_object_or_404(Meal, id=meal_id, author=request.user)

    if request.method == "POST":
        if request.POST.get("finish") == "1":
            return redirect("meals:meal_detail", meal_id=meal.id)

        food_id = request.POST.get("food") or request.POST.get("food_id")
        grams = request.POST.get("grams")

        if food_id and grams:
            food = get_object_or_404(Food, id=food_id)
            MealProducts.objects.create(meal=meal, food=food, grams=grams)

            return redirect(f"{request.path}?meal_id={meal.id}")

    foods = Food.objects.all().order_by("name")
    meal_products = MealProducts.objects.filter(meal=meal).select_related("food")
    return render(request, "meals/addFoodToMeal.html", {
        "meal": meal,
        "foods": foods,
        "meal_products": meal_products,
    })

def delete_meal_product(request, meal_id, meal_product_id):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    meal = get_object_or_404(Meal, id=meal_id, author=request.user)
    meal_product = get_object_or_404(MealProducts, id=meal_product_id, meal=meal)

    if request.method == "POST":
        meal_product.delete()

    redirect_to = request.POST.get("next") or request.GET.get("next")
    if redirect_to:
        return redirect(redirect_to)

    return redirect("meals:meal_detail", meal_id=meal.id)

def delete_meal(request, meal_id):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    meal = get_object_or_404(Meal, id=meal_id, author=request.user)

    if request.method == "POST":
        meal.delete()
        return redirect("meals:meals")

    return redirect("meals:meal_detail", meal_id=meal.id)

def toggle_favorite(request, meal_id):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    meal = get_object_or_404(Meal, id=meal_id)
    favorite, created = MealFavorites.objects.get_or_create(user=request.user, meal=meal)


    if not created:
        favorite.delete()
    
    meal.popularity = MealFavorites.objects.filter(meal=meal).count()
    meal.save()

    return redirect("meals:meal_detail", meal_id=meal.id)

def suggestions(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    all_tags = Tag.objects.order_by("type", "name")
    all_foods = Food.objects.order_by("name")

    grouped_tags = []
    selected_tag_ids = []
    for tag in all_tags:
        group_name = (tag.type or "Інше").strip() if tag.type else "Інше"
        is_selected = tag.id in selected_tag_ids
        if grouped_tags and grouped_tags[-1]["type"] == group_name:
            grouped_tags[-1]["tags"].append(tag)
            if is_selected:
                grouped_tags[-1]["has_selected"] = True
        else:
            grouped_tags.append({
                "type": group_name,
                "tags": [tag],
                "has_selected": is_selected,
            })

    selected_food_rows = []
    results = []
    was_submitted = request.method == "POST"
    min_match_percent = 0

    if request.method == "POST":
        raw_min_match = request.POST.get("min_match", "0")
        try:
            min_match_percent = int(raw_min_match)
        except (TypeError, ValueError):
            min_match_percent = 0
        min_match_percent = max(0, min(min_match_percent, 100))

        for raw_tag_id in request.POST.getlist("tag"):
            if str(raw_tag_id).isdigit():
                selected_tag_ids.append(int(raw_tag_id))

        selected_tag_ids_set = set(selected_tag_ids)
        grouped_tags = []
        for tag in all_tags:
            group_name = (tag.type or "Інше").strip() if tag.type else "Інше"
            is_selected = tag.id in selected_tag_ids_set
            if grouped_tags and grouped_tags[-1]["type"] == group_name:
                grouped_tags[-1]["tags"].append(tag)
                if is_selected:
                    grouped_tags[-1]["has_selected"] = True
            else:
                grouped_tags.append({
                    "type": group_name,
                    "tags": [tag],
                    "has_selected": is_selected,
                })

        grams_map = defaultdict(float)
        food_ids = request.POST.getlist("food_id")
        food_grams = request.POST.getlist("food_grams")
        parsed_food_ids = []

        for raw_food_id, raw_grams in zip(food_ids, food_grams):
            if not str(raw_food_id).isdigit():
                continue
            try:
                grams_value = float(str(raw_grams).replace(",", "."))
            except (TypeError, ValueError):
                continue

            if grams_value <= 0:
                continue

            food_id = int(raw_food_id)
            grams_map[food_id] += grams_value
            parsed_food_ids.append(food_id)

        selected_foods_qs = Food.objects.filter(id__in=parsed_food_ids)
        selected_foods_map = {food.id: food for food in selected_foods_qs}

        for food_id, grams_value in grams_map.items():
            food_obj = selected_foods_map.get(food_id)
            if not food_obj:
                continue
            selected_food_rows.append({
                "food_id": food_id,
                "food_name": food_obj.name,
                "food_type": food_obj.type,
                "grams": grams_value,
            })

        meals_qs = Meal.objects.all().prefetch_related("mealproducts_set__food")
        if selected_tag_ids:
            meals_qs = meals_qs.filter(mealtag__tag_id__in=selected_tag_ids).distinct()

        if selected_food_rows:
            for meal in meals_qs:
                meal_products = list(meal.mealproducts_set.all())
                if not meal_products:
                    continue

                required_total = sum(float(mp.grams) for mp in meal_products)
                if required_total <= 0:
                    continue

                covered_total = 0.0
                matched_items = 0
                missing = []

                calories = 0.0
                protein = 0.0
                carbs = 0.0
                fats = 0.0

                for mp in meal_products:
                    have = grams_map.get(mp.food_id, 0.0)
                    need = float(mp.grams)
                    covered_total += min(have, need)

                    if have > 0:
                        matched_items += 1

                    if have < need:
                        missing.append({
                            "name": mp.food.name,
                            "grams": round(need - have, 1),
                        })

                    if mp.food.grams > 0:
                        ratio = need / mp.food.grams
                        calories += mp.food.calories * ratio
                        protein += mp.food.protein * ratio
                        carbs += mp.food.carbs * ratio
                        fats += mp.food.fats * ratio

                coverage = (covered_total / required_total) * 100
                missing_items = len(missing)

                score = coverage - missing_items * 8 + meal.popularity * 0.2

                if coverage < min_match_percent:
                    continue

                results.append({
                    "meal": meal,
                    "score": round(score, 2),
                    "coverage": round(coverage, 1),
                    "matched_items": matched_items,
                    "total_items": len(meal_products),
                    "missing": missing,
                    "calories": round(calories),
                    "protein": round(protein),
                    "carbs": round(carbs),
                    "fats": round(fats),
                })

            results.sort(
                key=lambda item: (item["score"], item["coverage"], item["meal"].popularity),
                reverse=True,
            )
            results = results[:20]

    data = {
        "grouped_tags": grouped_tags,
        "foods": all_foods,
        "food_options": [
            {"id": food.id, "name": food.name, "type": food.type}
            for food in all_foods
        ],
        "selected_tag_ids": selected_tag_ids,
        "selected_food_rows": selected_food_rows,
        "min_match_percent": min_match_percent,
        "results": results,
        "was_submitted": was_submitted,
    }

    return render(request, "meals/mealSuggestions.html", data)