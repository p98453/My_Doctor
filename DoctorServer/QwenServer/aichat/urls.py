from django.urls import path
from . import views

# 二级路由
urlpatterns = {
    path('ai_chat_123/stream/', views.ai_chat_123, name='ai_chat_123'),
    path('chatlist/', views.chatlist, name='chatlist'),
    # chathistory
    path('chathistory/', views.chathistory, name='chathistory'),
    # delete_topic
    path('delete_topic/', views.delete_topic, name='delete_topic'),
}