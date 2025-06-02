from django.urls import path
from .views import dash_view, accounts_view, login_view, logout_view, transaction_delete, transaction_edit, transaction_new

urlpatterns = [
    path('', dash_view, name='dash'),
    path('dash/', dash_view, name='dash'),
    path('accounts/', accounts_view, name='accounts'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('transactions/delete/', transaction_delete, name='transaction_delete'),
    path('transactions/new/', transaction_new, name='transaction_new'),
    path('transactions/edit/<int:tx_id>/', transaction_edit, name='transaction_edit'),
]