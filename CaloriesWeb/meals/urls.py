from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.meals, name='meals'),
    path('<int:meal_id>/', views.meal_detail, name='meal_detail'),
    path("search/", views.search, name="search"),
]
