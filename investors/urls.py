# investors/urls.py
from django.urls import path
from . import views

app_name = 'investors'

urlpatterns = [
    # Main Views
    path('', views.portal_investor_list, name='portal-list'),
    path('add/', views.portal_investor_add, name='portal-add'),
    path('<int:pk>/', views.portal_investor_detail, name='portal-detail'),
    path('<int:pk>/upload-doc/', views.upload_investor_document, name='upload_doc'),
    path('verify-doc/<int:doc_pk>/', views.verify_document, name='verify_doc'),

    # Financial Operations
    path('<int:pk>/commitment/add/', views.add_commitment, name='add_commitment'),
]