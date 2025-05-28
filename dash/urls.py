from django.urls import path
from .views import dash_view, pages_view, posts_view, users_view, login_view

urlpatterns = [
    path('', dash_view, name='dash'),
    path('pages/', pages_view, name='pages'),
    path('posts/', posts_view, name='posts'),
    path('users/', users_view, name='users'),
    path('login/', login_view, name='login'),
]