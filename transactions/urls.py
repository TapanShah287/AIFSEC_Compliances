from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='portal-transactions'),
    path('add/commitment/', views.create_commitment, name='add-commitment'),
    path('add/call/', views.create_capital_call, name='add-call'),
    path('add/receipt/', views.create_receipt, name='add-receipt'),
    path('add/investment/', views.create_investment, name='add-investment'),
    path('add/redemption/', views.create_redemption, name='add-redemption'),
    path('add/distribution/', views.create_distribution, name='add-distribution'),
]