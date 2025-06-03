from django.urls import path
from .views import (
    dash_view,
    accounts_view,
    login_view,
    logout_view,
    transaction_delete,
    transaction_edit,
    transaction_new,
    account_delete,
    account_edit,
    account_new,
)

urlpatterns = [
    path('', dash_view, name='dash'),
    path('dash/', dash_view, name='dash'),
    path('accounts/', accounts_view, name='accounts'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('transaction/delete/', transaction_delete, name='transaction_delete'),
    path('transaction/new/', transaction_new, name='transaction_new'),
    path('transaction/edit/<int:tx_id>/', transaction_edit, name='transaction_edit'),
    path('account/delete/', account_delete, name='account_delete'),
    path('account/new/', account_new, name='account_new'),
    path('account/edit/<int:acc_id>/', account_edit, name='account_edit'),
]