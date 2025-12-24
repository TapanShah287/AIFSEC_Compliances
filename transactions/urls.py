from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('fund/<int:fund_pk>/purchase/add/', views.add_purchase, name='add_purchase'),
    path('fund/<int:fund_pk>/redemption/add/', views.add_redemption, name='add_redemption'),
]