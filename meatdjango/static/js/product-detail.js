(function () {
    const addButton = document.getElementById('product-add-to-cart');
    const successNode = document.getElementById('product-add-message');
    const errorNode = document.getElementById('product-add-error');

    if (!addButton || !window.SiteApi) {
        return;
    }

    addButton.addEventListener('click', async function () {
        const productId = Number(addButton.dataset.productId);
        if (!productId) {
            return;
        }

        addButton.disabled = true;
        successNode.hidden = true;
        errorNode.hidden = true;

        try {
            const response = await window.SiteApi.request('/api/cart/items/', {
                method: 'POST',
                body: JSON.stringify({ product_id: productId, quantity: 1 }),
            });

            window.SiteApi.updateCartBadge(response.cart.total_count);
            successNode.textContent = 'Товар добавлен в корзину';
            successNode.hidden = false;
        } catch (error) {
            errorNode.textContent = error.message || 'Не удалось добавить товар';
            errorNode.hidden = false;
        } finally {
            addButton.disabled = false;
        }
    });
})();
