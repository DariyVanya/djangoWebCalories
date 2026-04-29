from django.urls import path, include
from . import views

app_name = 'meals'

urlpatterns = [
    path('', views.meals, name='meals'),
    path('<int:meal_id>/', views.meal_detail, name='meal_detail'),
    path('<int:meal_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:meal_id>/delete/', views.delete_meal, name='delete_meal'),
    path('<int:meal_id>/products/<int:meal_product_id>/delete/', views.delete_meal_product, name='delete_meal_product'),
    path("search/", views.search, name="search"),
    path("add/", views.add_meal, name="add_meal"),
    path('add/addfood/', views.add_food_to_meal, name='add_food'),
    path('suggestions/', views.suggestions, name='suggestions'),
]
