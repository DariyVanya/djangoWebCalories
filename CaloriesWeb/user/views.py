from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from main.models import UserDetails
from meals.models import Meal, MealVerification
from .models import ManagerRequest


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
    details = get_object_or_404(UserDetails, user_id=user_id)
    manager_request = ManagerRequest.objects.filter(user=details.user).order_by("-created_at").first()
    user_meals = Meal.objects.filter(author=details.user).order_by("-id")
    verification_items = MealVerification.objects.filter(author=details.user).exclude(
        status="approved",
    ).order_by("-created_at")

    data = {
        'user_id': user_id,
        'details': details,
        'manager_request': manager_request,
        'user_meals': user_meals,
        'verification_items': verification_items,
    }

    return render(request, 'user/user_details.html', data)

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


def apply_manager(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    details = getattr(request.user, "details", None)
    if not details:
        return redirect("main:home")

    active_manager_count = UserDetails.objects.filter(role="manager", account_status="active").count()
    last_request = ManagerRequest.objects.filter(user=request.user).order_by("-created_at").first()

    manager_request_allowed = True
    reason = ""
    if details.is_banned:
        manager_request_allowed = False
        reason = "Ваш акаунт заблоковано"
    elif details.account_status != "active":
        manager_request_allowed = False
        reason = "Ваш акаунт неактивний"
    elif details.role in ("manager", "admin"):
        manager_request_allowed = False
        reason = "Ви вже маєте підвищену роль"
    elif details.current_streak < 100:
        manager_request_allowed = False
        reason = "Потрібна серія 100 днів"
    elif active_manager_count >= 10:
        manager_request_allowed = False
        reason = "В системі вже 10 активних менеджерів"
    elif last_request and last_request.status == "pending":
        manager_request_allowed = False
        reason = "Ваш запит вже на розгляді"

    if request.method == "POST":
        if not manager_request_allowed:
            return render(request, "user/apply_manager.html", {
                "details": details,
                "manager_request_allowed": manager_request_allowed,
                "reason": reason,
                "last_request": last_request,
            })

        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        motivation = (request.POST.get("motivation") or "").strip()
        resume = request.FILES.get("resume")

        if full_name and phone and motivation:
            ManagerRequest.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                motivation=motivation,
                resume=resume,
                status="pending",
            )
            return redirect("user:user_detail", user_id=request.user.id)

    return render(request, "user/apply_manager.html", {
        "details": details,
        "manager_request_allowed": manager_request_allowed,
        "reason": reason,
        "last_request": last_request,
    })


def manager_requests(request):
    if not request.user.is_authenticated:
        return redirect("main:logIn")

    details = getattr(request.user, "details", None)
    is_admin = bool(details and details.role == "admin") or getattr(request.user, "is_superuser", False)
    if not is_admin:
        return redirect("main:home")

    requests_qs = ManagerRequest.objects.select_related("user").order_by("-created_at")

    if request.method == "POST":
        request_id = request.POST.get("request_id")
        action = request.POST.get("action")
        comment = (request.POST.get("admin_comment") or "").strip()
        req_obj = get_object_or_404(ManagerRequest, id=request_id)

        if req_obj.status == "pending":
            if action == "approve":
                req_obj.status = "approved"
                target_details = getattr(req_obj.user, "details", None)
                if target_details:
                    target_details.role = "manager"
                    target_details.account_status = "active"
                    target_details.is_banned = False
                    target_details.save()
            elif action == "reject":
                req_obj.status = "rejected"
            elif action == "block":
                req_obj.status = "blocked"
                target_details = getattr(req_obj.user, "details", None)
                if target_details:
                    target_details.is_banned = True
                    target_details.save()

            req_obj.admin_comment = comment or None
            req_obj.reviewed_by = request.user
            req_obj.reviewed_at = timezone.now()
            req_obj.save()

        return redirect("user:manager_requests")

    return render(request, "user/manager_requests.html", {
        "requests": requests_qs,
    })
