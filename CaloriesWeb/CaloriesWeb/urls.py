
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path("meals/", include(('meals.urls', 'meals'), namespace='meals')),
    path("today/", include(('today.urls', 'today'), namespace='today')),
    path('', include(('main.urls', 'main'), namespace='main')),
    path("user/", include(('user.urls', 'user'), namespace='user')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
urlpatterns  += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
