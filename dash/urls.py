from django.urls import path
from .views import (
    dash_view,
    accounts_view,
    securities_view,
    settings_view,
    login_view,
    logout_view,
    transaction_new,
    account_delete,
    account_edit,
    account_new,
    securities_search,
    securities_add,
    transaction_update,
    transaction_create_form,
    transaction_edit_form
)

#Views
urlpatterns = [
    path('', dash_view, name='dash'),
    path('dashboard/', dash_view, name='dashboard'),

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('accounts/', accounts_view, name='accounts'),
    path('securities/', securities_view, name='securities'),
    path('settings/', settings_view, name='settings'),


]

#Forms
urlpatterns += [
    path('transaction/create/', transaction_create_form, name='transaction_create_form'),
    path('transaction/edit/<int:tx_id>/', transaction_edit_form, name='transaction_edit_form'),
]

#Apis
urlpatterns += [
    path('api/transaction/create/', transaction_new, name='api_transaction_create'),
    path('api/transaction/<int:tx_id>/', transaction_update, name='api_transaction_update'),  # PUT, PATCH, DELETE
    
    
    path('account/delete/', account_delete, name='account_delete'),
    path('account/new/', account_new, name='account_new'),
    path('account/edit/<int:acc_id>/', account_edit, name='account_edit'),
    path('api/securities_search/', securities_search, name='securities_search'),
    path('api/securities_add/', securities_add, name='securities_add'),
]