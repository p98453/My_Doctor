# 创建一个upload二级路由
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload, name='upload'),
]