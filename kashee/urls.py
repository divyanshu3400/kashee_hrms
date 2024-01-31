from django.contrib import admin
from django.urls import path,include
from hrms import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hrms.urls')),
    path('index/', views.home, name='index'),
]
