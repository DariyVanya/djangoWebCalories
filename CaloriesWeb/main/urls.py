
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('report/', views.report, name='report'),
    path("logIn/", views.logIn, name="logIn"),
    path("signUp/", views.signUp, name="signUp"),
    path("logOut/", views.logOut, name="logOut"),
]
