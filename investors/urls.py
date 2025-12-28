# investors/urls.py
from django.urls import path
from . import views

app_name = 'investors'

urlpatterns = [
    # Main Views
    path('', views.portal_investor_list, name='portal-list'),
    path('add/', views.portal_investor_add, name='portal-add'),
    path('<int:pk>/edit/', views.portal_investor_edit, name='portal-edit'),
    path('<int:pk>/', views.portal_investor_detail, name='portal-detail'),


    # Document Management
    path('<int:pk>/documents/upload/', views.investor_upload_doc, name='portal-upload-doc'),
    path('<int:pk>/bank/add/', views.investor_add_bank, name='portal-add-bank'),
    path('verify-doc/<int:doc_pk>/', views.verify_document, name='verify_doc'),

    # Financial Operations
    path('<int:pk>/commitment/add/', views.add_commitment, name='add_commitment'),
]