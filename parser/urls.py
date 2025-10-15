from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_files, name='upload_files'),
    path('results/<int:batch_id>/', views.view_results, name='view_results'),
]