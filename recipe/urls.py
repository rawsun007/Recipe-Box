"""
URL configuration for food project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2.  a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from recipe import views

urlpatterns = [

    path('delete_recipe/<int:id>/<str:source>/', views.delete_recipe, name='delete_recipe'), 
    path('add/', views.add, name='add'),
    path('update_recipe/<int:id>/', views.update_recipe, name='update_recipe'), 
    path('login_page/', views.login_page, name='login_page'),
    path('logout_page/', views.logout_page, name='logout_page'),
    path('signup/', views.signup, name='signup'),
    path('home/', views.home, name='home'),
    path('explore_recipes/', views.explore_recipes, name='explore_recipes'),
    path('user_pro/', views.user_pro, name='user_pro'),
    path('delete_profile/', views.delete_profile, name='delete_profile'),     
    path('save_user_recipe/', views.save_user_recipe, name='save_user_recipe'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
