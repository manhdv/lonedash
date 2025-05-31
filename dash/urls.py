from django.urls import path
from .views import dash_view, accounts_view, login_view, logout_view

urlpatterns = [
    path('', dash_view, name='dash'),
    path('dash/', dash_view, name='dash'),
    path('accounts/', accounts_view, name='accounts'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]