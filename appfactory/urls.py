from django.urls import path
from . import views

urlpatterns = [
    path('content/', views.product_list, name='read_excel'),
    path('upload/', views.view_upload, name='upload'),
    # path('product/<str:code>/', views.product_details, name='product_details'),
    path('process-files/', views.process_files, name='process_files'),
    path('xnt/', views.xnt, name='xnt'),
    
    path('success-upload/', views.success_upload, name='success_upload'),

    path('receive-product-id/', views.receive_product_id, name='receive_product_id'),
    path('xnt-receive-product-id/', views.xnt_receive_product_id, name='xnt_receive_product_id'),
    
    path('api/add-date/', views.add_date, name='add_date'),
    path('api/delete-date/', views.delete_date, name='delete_date'),
]
