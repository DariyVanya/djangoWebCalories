
from django.urls import path, include
from . import views

app_name = 'today'

urlpatterns = [
    path('', views.today, name='today'),
    path('add/', views.add_meal_today, name='addMeal'),
    path('delete/<int:entry_id>/', views.delete_today_entry, name='deleteTodayEntry')
]
