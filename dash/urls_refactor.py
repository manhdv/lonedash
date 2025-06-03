from django.urls import path
from .views import (
    dash_view,
    accounts_view,
    securities_view,
    settings_view,
    login_view,
    logout_view,
    transaction_delete,
    transaction_edit,
    transaction_new,
    account_delete,
    account_edit,
    account_new,
    securities_search,
    securities_add,
)

urlpatterns = [
    path('', dash_view, name='dash'),
    path('dashboard/', dash_view, name='dashboard'),

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('accounts/', accounts_view, name='accounts'),


    path('securities/', securities_view, name='securities'),
    path('settings/', settings_view, name='settings'),
]

urlpatterns += [
    # API endpoints
    path('api/transactions/', transaction_create, name='api_transaction_create'),  # POST
    path('api/transactions/<int:tx_id>/', transaction_update, name='api_transaction_update'),  # PUT/PATCH

    path('api/securities/search/', securities_search, name='api_securities_search'),
    path('api/securities/add/', securities_add, name='api_securities_add'),
    
    path('api/accounts/', account_create, name='api_account_create'),        # POST
    path('api/accounts/<int:acc_id>/', account_detail, name='api_account_detail'),  # GET, PUT, PATCH, DELETE
]