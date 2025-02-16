from django.contrib import admin
from django.urls import path, include
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('adminka', admin_dashboard, name='admin_board'),
    path('model/<str:model_name>/', model_list_view, name='model_list_view'),
    path('model/<str:model_name>/edit/', model_edit_view, name='model_edit_view'),
    path('model/<str:model_name>/edit/<int:object_id>/', model_edit_view, name='model_edit_view'),
    path('<str:model_name>/delete/<int:object_id>/', model_delete_view, name='model_delete_view'),
    path('export/<str:model_name>/', export_data, name='export_data'),
    path('import/<str:model_name>/', import_data, name='import_data'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)