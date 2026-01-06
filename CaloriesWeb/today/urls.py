
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.today, name='today'),
    path('add/', views.add_meal_today, name='addMeal')
]
