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
    entry_create_form,
    entry_edit_form,
    exit_create_form,
    exit_edit_form
)

from .apis import (
    api_transaction_create,
    api_transaction_update,
    api_account_create,
    api_account_update,
    api_security_search,
    api_security_add,
    api_security_update,
    api_entry_add,
    api_entry_update,
    api_exit_add,
    api_exit_update,
    api_portfolio_chart
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
    path('entry/create/', entry_create_form, name='entry_create_form'),
    path('entry/edit/<int:id>/', entry_edit_form, name='entry_edit_form'),

    path('exit/create/', exit_create_form, name='exit_create_form'),
    path('exit/edit/<int:id>/', exit_edit_form, name='exit_edit_form'),
]

#Apis
urlpatterns += [
    path('api/transaction/create/', api_transaction_create, name='api_transaction_create'),
    path('api/transaction/<int:id>/', api_transaction_update, name='api_transaction_update'),  # PUT, PATCH, DELETE
    path('api/account/create/', api_account_create, name='api_account_create'),
    path('api/account/<int:id>/', api_account_update, name='api_account_update'),  # PUT, PATCH, DELETE    
    
    path('api/security/search/', api_security_search, name='api_security_search'),
    path('api/security/add/', api_security_add, name='api_security_add'),
    path('api/security/<int:id>/', api_security_update, name='api_security_update'),  # PUT, PATCH, DELETE

    path('api/entry/add/', api_entry_add, name='api_entry_add'),
    path('api/entry/<int:id>/', api_entry_update, name='api_entry_update'),

    path('api/exit/add/', api_exit_add, name='api_exit_add'),
    path('api/exit/<int:id>/', api_exit_update, name='api_exit_update'),

    path('api/portfolio/data/', api_portfolio_chart, name='api_portfolio_chart'),
]