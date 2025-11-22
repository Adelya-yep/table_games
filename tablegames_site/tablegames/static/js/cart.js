// static/js/cart.js
document.addEventListener('DOMContentLoaded', function() {
    // Функция для добавления в корзину
    function addToCart(gameId, gameName) {
        fetch(`/cart/add/${gameId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Показываем уведомление
                showNotification(`"${gameName}" добавлен в корзину`, 'success');

                // Обновляем счетчик в навбаре
                updateCartCounter(data.cart_total);
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Ошибка при добавлении в корзину', 'error');
        });
    }

    // Функция для показа уведомлений
    function showNotification(message, type) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Функция для обновления счетчика корзины
    function updateCartCounter(count) {
        let cartCounter = document.getElementById('cart-counter');
        if (!cartCounter) {
            // Создаем счетчик если его нет
            const cartLink = document.querySelector('a[href*="cart"]');
            if (cartLink) {
                cartCounter = document.createElement('span');
                cartCounter.id = 'cart-counter';
                cartCounter.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
                cartLink.appendChild(cartCounter);
            }
        }

        if (cartCounter) {
            cartCounter.textContent = count;
            cartCounter.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    // Функция для получения CSRF токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Обработчики для кнопок "В корзину"
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const gameId = this.dataset.gameId;
            const gameName = this.dataset.gameName;
            addToCart(gameId, gameName);
        });
    });

    // Загружаем начальное количество товаров в корзине
    if (document.querySelector('.add-to-cart-btn')) {
        fetch('/cart/count/')
            .then(response => response.json())
            .then(data => {
                updateCartCounter(data.count);
            });
    }
});