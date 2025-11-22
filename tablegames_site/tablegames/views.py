from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Game, GameTable, TableBooking, GameRental, PurchaseOrder, Customer, OrderItem, Cart, CartItem
from .forms import TableBookingForm, GameRentalForm, PurchaseOrderForm, CustomerForm, CustomUserCreationForm, LoginForm, OrderConfirmationForm
from decimal import Decimal
import datetime
import json

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


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            Customer.objects.create(
                user=user,
                phone='',
                address=''
            )

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать в TableGames!')
            return redirect('index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'tablegames/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()

    return render(request, 'tablegames/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('index')


@login_required
def create_booking(request):
    if request.method == 'POST':
        form = TableBookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)

                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    booking.customer = customer

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

                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    rental.customer = customer

                    rental_days = (rental.rental_end_date - rental.rental_start_date).days
                    rental.total_price = rental.game.rental_price_per_day * rental_days * rental.quantity
                    rental.save()

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

                    customer, created = Customer.objects.get_or_create(
                        user=request.user,
                        defaults={'phone': '', 'address': ''}
                    )
                    order.customer = customer
                    order.total_amount = Decimal('0.00')
                    order.save()

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


@login_required
def add_to_cart(request, game_id):
    if request.method == 'POST':
        try:
            game = get_object_or_404(Game, id=game_id)
            cart, created = Cart.objects.get_or_create(user=request.user)

            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                game=game,
                defaults={'quantity': 1}
            )

            if not item_created:
                if cart_item.quantity < game.in_stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Нельзя добавить больше {game.in_stock} шт. этого товара'
                    })

            return JsonResponse({
                'success': True,
                'message': 'Товар добавлен в корзину',
                'cart_total': cart.total_items
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при добавлении в корзину'
            })

    return JsonResponse({'success': False, 'message': 'Неверный запрос'})


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

            if action == 'increase':
                if cart_item.quantity < cart_item.game.in_stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Нельзя добавить больше {cart_item.game.in_stock} шт. этого товара'
                    })
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
                    return JsonResponse({
                        'success': True,
                        'message': 'Товар удален из корзины',
                        'deleted': True
                    })
            elif action == 'remove':
                cart_item.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Товар удален из корзины',
                    'deleted': True
                })

            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'quantity': cart_item.quantity,
                'item_total': float(cart_item.total_price),
                'cart_total': float(cart.total_price),
                'cart_items_count': cart.total_items
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при обновлении корзины'
            })

    return JsonResponse({'success': False, 'message': 'Неверный запрос'})


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('game').all()

    return render(request, 'tablegames/cart.html', {
        'cart': cart,
        'items': items
    })


@login_required
def create_order_from_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('game').all()

    if not items:
        messages.error(request, 'Корзина пуста')
        return redirect('cart_view')

    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderConfirmationForm(request.user, request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Проверяем доступность товаров
                    for item in items:
                        if item.quantity > item.game.in_stock:
                            messages.error(request,
                                           f'Товар "{item.game.name}" недоступен в количестве {item.quantity} шт.')
                            return redirect('cart_view')

                    # Создаем заказ
                    total_amount = sum(item.total_price for item in items)
                    order = PurchaseOrder.objects.create(
                        customer=customer,
                        total_amount=total_amount,
                        shipping_address=customer.address
                    )

                    # Создаем элементы заказа
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            game=item.game,
                            quantity=item.quantity,
                            price=item.game.price
                        )

                        # Уменьшаем количество на складе
                        item.game.in_stock -= item.quantity
                        item.game.save()

                    # Очищаем корзину
                    cart.items.all().delete()

                    messages.success(request, f'Заказ #{order.order_number} успешно создан!')
                    return redirect('order_success', order_id=order.id)

            except Exception as e:
                messages.error(request, f'Ошибка при создании заказа: {str(e)}')
        else:
            messages.error(request, 'Неверный пароль')

    else:
        form = OrderConfirmationForm(request.user)

    return render(request, 'tablegames/create_order.html', {
        'cart': cart,
        'items': items,
        'form': form,
        'customer': customer
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id, customer__user=request.user)
    return render(request, 'tablegames/order_success.html', {'order': order})


@login_required
def order_list(request):
    customer, created = Customer.objects.get_or_create(user=request.user)
    orders = PurchaseOrder.objects.filter(customer=customer).prefetch_related('items__game')

    return render(request, 'tablegames/order_list.html', {'orders': orders})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id, customer__user=request.user)

    if order.status == 'new':
        try:
            with transaction.atomic():
                # Возвращаем товары на склад
                for item in order.items.all():
                    item.game.in_stock += item.quantity
                    item.game.save()

                order.status = 'cancelled'
                order.save()
                messages.success(request, f'Заказ #{order.order_number} отменен')
        except Exception as e:
            messages.error(request, 'Ошибка при отмене заказа')
    else:
        messages.error(request, 'Можно отменять только новые заказы')

    return redirect('order_list')


def get_cart_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return JsonResponse({'count': cart.total_items})
    return JsonResponse({'count': 0})