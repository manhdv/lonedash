from django.urls import path
from .views import (
    dash_view,
    accounts_view,
    securities_view,
    settings_view,
    trades_view,
    login_view,
    logout_view,
    account_edit_form,
    account_create_form,
    transaction_create_form,
    transaction_edit_form,
    security_search_form,
    trade_create_form
    
)

from .apis import (
    transaction_create_api,
    transaction_update_api,
    account_create_api,
    account_update_api,
    security_search_api,
    security_add_api,
    security_update_api,
    entry_add_api,
    entry_update_api
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
    path('trades/', trades_view, name='trades'),


]

#Forms
urlpatterns += [
    path('transaction/create/', transaction_create_form, name='transaction_create_form'),
    path('transaction/edit/<int:id>/', transaction_edit_form, name='transaction_edit_form'),

    path('account/create/', account_create_form, name='account_create_form'),
    path('account/edit/<int:id>/', account_edit_form, name='account_edit_form'),

    path('security/search/', security_search_form, name='security_search_form'),
    path('trade/create/', trade_create_form, name='trade_create_form'),
]

#Apis
urlpatterns += [
    path('api/transaction/create/', transaction_create_api, name='transaction_create_api'),
    path('api/transaction/<int:id>/', transaction_update_api, name='transaction_update_api'),  # PUT, PATCH, DELETE
    path('api/account/create/', account_create_api, name='account_create_api'),
    path('api/account/<int:id>/', account_update_api, name='account_update_api'),  # PUT, PATCH, DELETE    
    
    path('api/security/search/', security_search_api, name='security_search_api'),
    path('api/security/add/', security_add_api, name='security_add_api'),
    path('api/security/<int:id>/', security_update_api, name='security_update_api'),  # PUT, PATCH, DELETE

    path('api/entry/add/', entry_add_api, name='entry_add_api'),
    path('api/entry/<int:id>/', entry_update_api, name='entry_update_api'),
]