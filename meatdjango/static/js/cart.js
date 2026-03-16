(function () {
    const container = document.getElementById('cart-items');
    const totalNode = document.getElementById('cart-total');
    const emptyNode = document.getElementById('cart-empty');
    const checkoutButton = document.getElementById('cart-checkout-button');

    if (!container || !totalNode || !emptyNode || !checkoutButton) {
        return;
    }

    function renderCartItem(item) {
        const wrapper = document.createElement('div');
        wrapper.className = 'cart-item';
        wrapper.dataset.productId = String(item.product.id);

        wrapper.innerHTML = `
            <div class="cart-item-info">
                ${item.product.image_url ? `<img src="${item.product.image_url}" alt="${item.product.name}" class="cart-item-image">` : ''}
                <div>
                    <h3>${item.product.name}</h3>
                    <p>Цена за единицу: ${window.SiteApi.formatPrice(item.product.price)} ₽</p>
                    <p><strong>Итого: ${window.SiteApi.formatPrice(item.item_total)} ₽</strong></p>
                </div>
            </div>
            <div class="cart-actions">
                <div class="quantity-controls">
                    <button type="button" class="qty-btn" data-action="decrease">−</button>
                    <span class="qty-number">${item.quantity}</span>
                    <button type="button" class="qty-btn" data-action="increase">+</button>
                </div>
                <button type="button" class="remove-link" data-action="remove">Удалить</button>
            </div>
        `;

        return wrapper;
    }

    function applyCart(cart) {
        container.innerHTML = '';

        if (!cart.items.length) {
            emptyNode.hidden = false;
            checkoutButton.hidden = true;
            totalNode.textContent = '';
        } else {
            emptyNode.hidden = true;
            checkoutButton.hidden = false;
            for (const item of cart.items) {
                container.appendChild(renderCartItem(item));
            }
            totalNode.textContent = `Общая сумма: ${window.SiteApi.formatPrice(cart.total_price)} ₽`;
        }

        window.SiteApi.updateCartBadge(cart.total_count);
    }

    async function loadCart() {
        const cart = await window.SiteApi.request('/api/cart/');
        applyCart(cart);
    }

    async function patchQuantity(productId, quantity) {
        const response = await window.SiteApi.request(`/api/cart/items/${productId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ quantity }),
        });

        applyCart(response.cart);
    }

    async function removeItem(productId) {
        const response = await window.SiteApi.request(`/api/cart/items/${productId}/remove/`, {
            method: 'DELETE',
        });

        applyCart(response.cart);
    }

    container.addEventListener('click', async function (event) {
        const actionButton = event.target.closest('[data-action]');
        if (!actionButton) {
            return;
        }

        const row = event.target.closest('.cart-item');
        if (!row) {
            return;
        }

        const productId = Number(row.dataset.productId);
        const currentQty = Number(row.querySelector('.qty-number').textContent || '1');

        try {
            if (actionButton.dataset.action === 'increase') {
                await patchQuantity(productId, currentQty + 1);
            }
            if (actionButton.dataset.action === 'decrease') {
                await patchQuantity(productId, currentQty - 1);
            }
            if (actionButton.dataset.action === 'remove') {
                await removeItem(productId);
            }
        } catch (error) {
            alert(error.message);
        }
    });

    loadCart().catch(function (error) {
        alert(error.message);
    });
})();
