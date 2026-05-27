from main.models import UserDetails
from user.models import ManagerRequest


def role_context(request):
    if not request.user.is_authenticated:
        return {
            "is_admin": False,
            "is_manager": False,
            "manager_request_allowed": False,
            "manager_request_reason": "",
        }

    details = getattr(request.user, "details", None)
    if not details:
        return {
            "is_admin": False,
            "is_manager": False,
            "manager_request_allowed": False,
            "manager_request_reason": "",
        }

    is_active_staff = details.account_status == "active" and not details.is_banned
    is_admin = is_active_staff and (details.role == "admin" or getattr(request.user, "is_superuser", False))
    is_manager = is_active_staff and details.role == "manager"

    active_manager_count = UserDetails.objects.filter(
        role="manager",
        account_status="active",
        is_banned=False,
    ).count()

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

    return {
        "is_admin": is_admin,
        "is_manager": is_manager,
        "manager_request_allowed": manager_request_allowed,
        "manager_request_reason": reason,
    }
