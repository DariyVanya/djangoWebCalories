
from django.urls import path, include
from . import views

app_name = 'user'

urlpatterns = [
    path('<int:user_id>/', views.user_details, name='user_detail'),
    path('<int:user_id>/edit/', views.edit_profile, name='edit_profile'),
]
