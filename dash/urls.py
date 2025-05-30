from django.urls import path
from .views import dash_view, accounts_view

urlpatterns = [
    path('', dash_view, name='dash'),
    path('dash/', dash_view, name='dash'),
    path('accounts/', accounts_view, name='accounts'),
]