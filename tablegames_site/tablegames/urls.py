from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('games/', views.game_list, name='game_list'),
    path('games/<int:game_id>/', views.game_detail, name='game_detail'),
    path('tables/', views.table_list, name='table_list'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('rental/create/', views.create_rental, name='create_rental'),
    path('rental/create/<int:game_id>/', views.create_rental, name='create_rental_game'),
    path('rental/success/<int:rental_id>/', views.rental_success, name='rental_success'),
    path('profile/', views.profile, name='profile'),

    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:game_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('order/create/', views.create_order_from_cart, name='create_order_from_cart'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('cart/count/', views.get_cart_count, name='get_cart_count'),

    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
]