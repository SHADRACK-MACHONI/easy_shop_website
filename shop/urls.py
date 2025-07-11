from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-product/', views.add_product, name='add_product'),
    path('update-order/<int:pk>/<str:status>/', views.update_order_status, name='update_order_status'),
    path('pay/<int:order_id>/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('admin/mark-out-for-delivery/<int:order_id>/', views.mark_out_for_delivery, name='mark_out_for_delivery'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('mark-delivered/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
    path('mark-delivered/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
    path('pay/<int:pk>/', views.initiate_payment, name='initiate_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]

