from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic.base import RedirectView

handler404 = 'recipe.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recipe/', include('recipe.urls')),
    path('', RedirectView.as_view(url='/recipe/explore_recipes/', permanent=True)),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        success_url='/password_reset_done/'
    ), name='password_reset'),

    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)