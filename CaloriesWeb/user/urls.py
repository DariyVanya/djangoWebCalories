
from django.urls import path, include
from . import views

app_name = 'user'

urlpatterns = [
    path('<int:user_id>/', views.user_details, name='user_detail'),
    path('<int:user_id>/edit/', views.edit_profile, name='edit_profile'),
    path('apply-manager/', views.apply_manager, name='apply_manager'),
    path('manager-requests/', views.manager_requests, name='manager_requests'),
]
