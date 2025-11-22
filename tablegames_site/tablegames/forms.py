from django import forms
from django.core.exceptions import ValidationError
from .models import TableBooking, GameRental, PurchaseOrder, Customer
from django.utils import timezone
import datetime


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TableBookingForm(forms.ModelForm):
    class Meta:
        model = TableBooking
        fields = ['table', 'booking_date', 'start_time', 'end_time', 'number_of_people']
        widgets = {
            'table': forms.Select(attrs={'class': 'form-control'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'number_of_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        table = cleaned_data.get('table')
        number_of_people = cleaned_data.get('number_of_people')

        if booking_date and start_time and end_time:
            if booking_date < timezone.now().date():
                raise ValidationError('Нельзя забронировать столик на прошедшую дату')

            if start_time >= end_time:
                raise ValidationError('Время окончания должно быть позже времени начала')

            # Проверка доступности столика
            if TableBooking.objects.filter(
                    table=table,
                    booking_date=booking_date,
                    start_time__lt=end_time,
                    end_time__gt=start_time,
                    status__in=['pending', 'confirmed']
            ).exists():
                raise ValidationError('Этот столик уже забронирован на выбранное время')

        if number_of_people and table:
            if number_of_people > table.capacity:
                raise ValidationError(f'Этот столик вмещает максимум {table.capacity} человек')

        return cleaned_data


class GameRentalForm(forms.ModelForm):
    class Meta:
        model = GameRental
        fields = ['game', 'rental_start_date', 'rental_end_date', 'quantity']
        widgets = {
            'game': forms.Select(attrs={'class': 'form-control'}),
            'rental_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rental_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rental_start_date = cleaned_data.get('rental_start_date')
        rental_end_date = cleaned_data.get('rental_end_date')
        game = cleaned_data.get('game')
        quantity = cleaned_data.get('quantity')

        if rental_start_date and rental_end_date:
            if rental_start_date < timezone.now().date():
                raise ValidationError('Дата начала аренды не может быть в прошлом')

            if rental_end_date <= rental_start_date:
                raise ValidationError('Дата окончания аренды должна быть позже даты начала')

            rental_days = (rental_end_date - rental_start_date).days
            if rental_days > 30:
                raise ValidationError('Максимальный срок аренды - 30 дней')

        if game and quantity:
            if quantity > game.available_for_rental:
                raise ValidationError(f'Доступно для аренды только {game.available_for_rental} экземпляров')

        return cleaned_data


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['shipping_address']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }