(function () {
    const form = document.getElementById('checkout-form');
    const itemsNode = document.getElementById('checkout-items');
    const totalNode = document.getElementById('checkout-total');
    const emptyNode = document.getElementById('checkout-empty');

    if (!form || !itemsNode || !totalNode || !emptyNode) {
        return;
    }

    function renderItems(items) {
        itemsNode.innerHTML = '';
        for (const item of items) {
            const row = document.createElement('p');
            row.textContent = `${item.product.name} — ${item.quantity} шт. — ${window.SiteApi.formatPrice(item.item_total)} ₽`;
            itemsNode.appendChild(row);
        }
    }

    async function loadCart() {
        const cart = await window.SiteApi.request('/api/cart/');

        if (!cart.items.length) {
            emptyNode.hidden = false;
            form.querySelector('button[type="submit"]').disabled = true;
            itemsNode.innerHTML = '';
            totalNode.textContent = '';
            window.SiteApi.updateCartBadge(0);
            return;
        }

        emptyNode.hidden = true;
        form.querySelector('button[type="submit"]').disabled = false;
        renderItems(cart.items);
        totalNode.textContent = `Общая сумма: ${window.SiteApi.formatPrice(cart.total_price)} ₽`;
        window.SiteApi.updateCartBadge(cart.total_count);
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        const payload = {
            full_name: form.full_name.value.trim(),
            phone: form.phone.value.trim(),
            email: form.email.value.trim(),
            address: form.address.value.trim(),
        };

        try {
            const response = await window.SiteApi.request('/api/orders/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            window.SiteApi.updateCartBadge(0);
            window.location.href = response.redirect_url;
        } catch (error) {
            alert(error.message);
        }
    });

    loadCart().catch(function (error) {
        alert(error.message);
    });
})();
