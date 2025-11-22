from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Game, GameTable, TableBooking, GameRental, PurchaseOrder, Customer, OrderItem
from .forms import TableBookingForm, GameRentalForm, PurchaseOrderForm, CustomerForm
from decimal import Decimal
import datetime


def index(request):
    games = Game.objects.filter(in_stock__gt=0)[:6]
    tables = GameTable.objects.filter(is_active=True)
    return render(request, 'tablegames/index.html', {
        'games': games,
        'tables': tables
    })


def game_list(request):
    games = Game.objects.all()
    category = request.GET.get('category')
    if category:
        games = games.filter(category=category)

    return render(request, 'tablegames/game_list.html', {
        'games': games,
        'category': category
    })


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return render(request, 'tablegames/game_detail.html', {'game': game})


def table_list(request):
    tables = GameTable.objects.filter(is_active=True)
    return render(request, 'tablegames/table_list.html', {'tables': tables})


@login_required
def create_booking(request):
    if request.method == 'POST':
        form = TableBookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)

                    # Получаем или создаем клиента
                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    booking.customer = customer

                    # Рассчитываем стоимость
                    duration_hours = (datetime.datetime.combine(
                        booking.booking_date, booking.end_time
                    ) - datetime.datetime.combine(
                        booking.booking_date, booking.start_time
                    )).seconds / 3600

                    booking.total_price = Decimal(
                        duration_hours) * booking.table.price_per_hour_per_person * booking.number_of_people
                    booking.save()

                    messages.success(request, 'Столик успешно забронирован!')
                    return redirect('booking_success', booking_id=booking.id)

            except Exception as e:
                messages.error(request, f'Произошла ошибка при бронировании: {str(e)}')
    else:
        form = TableBookingForm()

    return render(request, 'tablegames/booking_create.html', {'form': form})


@login_required
def create_rental(request, game_id=None):
    game = None
    if game_id:
        game = get_object_or_404(Game, id=game_id)

    if request.method == 'POST':
        form = GameRentalForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    rental = form.save(commit=False)

                    # Получаем или создаем клиента
                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    rental.customer = customer

                    # Рассчитываем стоимость
                    rental_days = (rental.rental_end_date - rental.rental_start_date).days
                    rental.total_price = rental.game.rental_price_per_day * rental_days * rental.quantity
                    rental.save()

                    # Обновляем доступное количество
                    game = rental.game
                    game.available_for_rental -= rental.quantity
                    game.save()

                    messages.success(request, 'Игра успешно арендована!')
                    return redirect('rental_success', rental_id=rental.id)

            except Exception as e:
                messages.error(request, f'Произошла ошибка при аренде: {str(e)}')
    else:
        initial = {}
        if game:
            initial['game'] = game
        form = GameRentalForm(initial=initial)

    return render(request, 'tablegames/rental_create.html', {'form': form, 'game': game})


@login_required
def create_order(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)

                    # Получаем или создаем клиента
                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    order.customer = customer
                    order.total_amount = Decimal('0.00')
                    order.save()

                    # Здесь должна быть логика добавления игр в корзину
                    # В реальном приложении нужно использовать сессии для корзины

                    messages.success(request, 'Заказ создан!')
                    return redirect('index')

            except Exception as e:
                messages.error(request, f'Произошла ошибка при создании заказа: {str(e)}')
    else:
        form = PurchaseOrderForm()

    return render(request, 'tablegames/order_create.html', {'form': form})


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(TableBooking, id=booking_id, customer__user=request.user)
    return render(request, 'tablegames/booking_success.html', {'booking': booking})


@login_required
def rental_success(request, rental_id):
    rental = get_object_or_404(GameRental, id=rental_id, customer__user=request.user)
    rental_days = (rental.rental_end_date - rental.rental_start_date).days
    return render(request, 'tablegames/rental_success.html', {
        'rental': rental,
        'rental_days': rental_days
    })


@login_required
def profile(request):
    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = CustomerForm(instance=customer)

    bookings = TableBooking.objects.filter(customer=customer)
    rentals = GameRental.objects.filter(customer=customer)
    orders = PurchaseOrder.objects.filter(customer=customer)

    return render(request, 'tablegames/profile.html', {
        'form': form,
        'bookings': bookings,
        'rentals': rentals,
        'orders': orders,
    })