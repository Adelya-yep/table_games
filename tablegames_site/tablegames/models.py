from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Game(models.Model):
    GAME_CATEGORIES = [
        ('strategy', 'Стратегические'),
        ('family', 'Семейные'),
        ('party', 'Для вечеринок'),
        ('cooperative', 'Кооперативные'),
        ('card', 'Карточные'),
        ('rpg', 'Ролевые'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название игры')
    description = models.TextField(verbose_name='Описание')
    category = models.CharField(max_length=20, choices=GAME_CATEGORIES, verbose_name='Категория')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена покупки')
    rental_price_per_day = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Цена аренды за день')
    min_players = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                              verbose_name='Минимальное количество игроков')
    max_players = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                              verbose_name='Максимальное количество игроков')
    play_time_minutes = models.PositiveIntegerField(verbose_name='Время игры (минуты)')
    difficulty = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Сложность (1-5)'
    )
    in_stock = models.PositiveIntegerField(default=0, verbose_name='В наличии для покупки')
    available_for_rental = models.PositiveIntegerField(default=0, verbose_name='Доступно для аренды')
    image = models.ImageField(upload_to='games/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return self.name


class GameTable(models.Model):
    TABLE_TYPES = [
        ('small', 'Маленький (2-4 человека)'),
        ('medium', 'Средний (4-6 человек)'),
        ('large', 'Большой (6-8 человек)'),
        ('vip', 'VIP (8+ человек)'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название столика')
    table_type = models.CharField(max_length=10, choices=TABLE_TYPES, verbose_name='Тип столика')
    capacity = models.PositiveIntegerField(verbose_name='Вместимость')
    price_per_hour_per_person = models.DecimalField(max_digits=6, decimal_places=2, default=60.00,
                                                    verbose_name='Цена за час за человека')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Игровой столик'
        verbose_name_plural = 'Игровые столики'

    def __str__(self):
        return f"{self.name} ({self.get_table_type_display()})"


class Customer(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    address = models.TextField(verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class TableBooking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент')
    table = models.ForeignKey(GameTable, on_delete=models.CASCADE, verbose_name='Столик')
    booking_date = models.DateField(verbose_name='Дата бронирования')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    number_of_people = models.PositiveIntegerField(verbose_name='Количество человек')
    total_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Общая стоимость')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидание'),
            ('confirmed', 'Подтверждено'),
            ('cancelled', 'Отменено'),
            ('completed', 'Завершено'),
        ],
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Бронирование столика'
        verbose_name_plural = 'Бронирования столиков'
        unique_together = ['table', 'booking_date', 'start_time']

    def __str__(self):
        return f"Бронирование {self.table.name} на {self.booking_date}"


class GameRental(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='Игра')
    rental_start_date = models.DateField(verbose_name='Дата начала аренды')
    rental_end_date = models.DateField(verbose_name='Дата окончания аренды')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    total_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Общая стоимость')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидание'),
            ('active', 'Активна'),
            ('completed', 'Завершена'),
            ('cancelled', 'Отменена'),
        ],
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Аренда игры'
        verbose_name_plural = 'Аренды игр'

    def __str__(self):
        return f"Аренда {self.game.name} - {self.customer}"


class PurchaseOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент')
    games = models.ManyToManyField(Game, through='OrderItem', verbose_name='Игры')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая сумма')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидание'),
            ('confirmed', 'Подтвержден'),
            ('shipped', 'Отправлен'),
            ('delivered', 'Доставлен'),
            ('cancelled', 'Отменен'),
        ],
        default='pending',
        verbose_name='Статус'
    )
    shipping_address = models.TextField(verbose_name='Адрес доставки')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Заказ на покупку'
        verbose_name_plural = 'Заказы на покупку'

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer}"


class OrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, verbose_name='Заказ')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='Игра')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.game.name} x{self.quantity}"