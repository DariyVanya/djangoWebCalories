# from django.contrib import admin
# from .models import User

#admin.site.register(User)

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import UserDetails

User = get_user_model()

class UserDetailsInline(admin.StackedInline):
    model = UserDetails
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (UserDetailsInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
