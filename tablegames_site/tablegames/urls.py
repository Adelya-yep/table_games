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
    path('order/create/', views.create_order, name='create_order'),
    path('profile/', views.profile, name='profile'),
]