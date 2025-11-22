from django.contrib import admin
from .models import Game, GameTable, Customer, TableBooking, GameRental, PurchaseOrder, OrderItem

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'rental_price_per_day', 'in_stock', 'available_for_rental']
    list_filter = ['category', 'difficulty']
    search_fields = ['name', 'description']

@admin.register(GameTable)
class GameTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'table_type', 'capacity', 'price_per_hour_per_person', 'is_active']
    list_filter = ['table_type', 'is_active']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']

@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'table', 'booking_date', 'start_time', 'end_time', 'total_price', 'status']
    list_filter = ['status', 'booking_date']
    search_fields = ['customer__user__username', 'table__name']

@admin.register(GameRental)
class GameRentalAdmin(admin.ModelAdmin):
    list_display = ['customer', 'game', 'rental_start_date', 'rental_end_date', 'total_price', 'status']
    list_filter = ['status', 'rental_start_date']
    search_fields = ['customer__user__username', 'game__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__user__username']
    inlines = [OrderItemInline]