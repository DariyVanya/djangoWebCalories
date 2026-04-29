from django.shortcuts import render,redirect
from main.models import UserDetails


CALORIE_PLAN_SHIFT = {
    'cut': -250,
    'maintain': 0,
    'bulk': 250,
}


def _to_int(value, fallback):
    try:
        if value is None:
            return fallback
        normalized = str(value).strip().replace(',', '.')
        return int(float(normalized))
    except (TypeError, ValueError):
        return fallback


def _to_float(value, fallback):
    try:
        if value is None:
            return fallback
        normalized = str(value).strip().replace(',', '.')
        return float(normalized)
    except (TypeError, ValueError):
        return fallback


def _round_to_nearest_hundred(value):
    return int(round(value / 100.0) * 100)




def _calculate_goal_calories(sex, age, height_cm, weight_kg, activity_level, calorie_plan):
    if sex == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    factors = {1: 1.2, 2: 1.375, 3: 1.55, 4: 1.725, 5: 1.9}
    maintenance = bmr * factors.get(activity_level, 1.2)
    adjusted = maintenance + CALORIE_PLAN_SHIFT.get(calorie_plan, 0)
    return max(1000, _round_to_nearest_hundred(adjusted))


def user_details(request, user_id):
    
    # if request.user.is_authenticated and request.user.id == user_id:

        data = {
            'user_id': user_id,
            'details': UserDetails.objects.get(user_id=user_id)

        }

        return render(request, 'user/user_details.html', data)
    # else:
    #     return redirect('main:logIn')

def edit_profile(request, user_id):
    if request.user.is_authenticated and request.user.id == user_id:
        details = UserDetails.objects.get(user_id=user_id)
        profile_user = details.user

        if request.method == 'POST':
            profile_user.first_name = request.POST.get('first_name', profile_user.first_name).strip()
            profile_user.last_name = request.POST.get('last_name', profile_user.last_name).strip()
            profile_user.save()

            details.sex = request.POST.get('sex', details.sex)
            details.age = _to_int(request.POST.get('age'), details.age)
            details.height_cm = _to_int(request.POST.get('height_cm'), details.height_cm)
            details.weight_kg = _to_float(request.POST.get('weight_kg'), details.weight_kg)
            details.activity_level = _to_int(request.POST.get('activity_level'), details.activity_level)
            details.calorie_plan = request.POST.get('calorie_plan', details.calorie_plan)

            details.goal_calories = _calculate_goal_calories(
                details.sex,
                details.age,
                details.height_cm,
                details.weight_kg,
                details.activity_level,
                details.calorie_plan,
            )

            details.save()

            return redirect('user:user_detail', user_id=user_id)

        data = {
            'user_id': user_id,
            'details': details,
        }
        return render(request, 'user/edit_profile.html', data)
    else:
        return redirect('main:logIn')
