(function () {
    const usernameNode = document.getElementById('profile-username');
    const emailWrapNode = document.getElementById('profile-email-wrap');
    const emailNode = document.getElementById('profile-email');
    const ordersNode = document.getElementById('profile-orders');
    const ordersEmptyNode = document.getElementById('profile-orders-empty');
    const reviewsNode = document.getElementById('profile-reviews');
    const reviewsEmptyNode = document.getElementById('profile-reviews-empty');

    if (!usernameNode || !ordersNode || !reviewsNode) {
        return;
    }

    function escapeHtml(value) {
        return String(value || '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function renderOrders(orders) {
        ordersNode.innerHTML = '';

        if (!orders.length) {
            ordersEmptyNode.hidden = false;
            return;
        }

        ordersEmptyNode.hidden = true;

        for (const order of orders) {
            const card = document.createElement('article');
            card.className = 'order-card';

            const itemsHtml = (order.items || [])
                .map(function (item) {
                    return `<li>${escapeHtml(item.product_name)} — ${item.quantity} шт.</li>`;
                })
                .join('');

            card.innerHTML = `
                <div class="order-header">
                    <strong>Заказ #${order.id}</strong>
                    <span class="order-status ${order.status_css_class}">${escapeHtml(order.status_display)}</span>
                </div>
                <p class="order-meta">Дата: ${escapeHtml(order.created_at_display)}</p>
                <p class="order-meta">Сумма: ${window.SiteApi.formatPrice(order.total_price)} ₽</p>
                <ul class="order-items">${itemsHtml}</ul>
            `;

            ordersNode.appendChild(card);
        }
    }

    function renderReviews(reviews) {
        reviewsNode.innerHTML = '';

        if (!reviews.length) {
            reviewsEmptyNode.hidden = false;
            return;
        }

        reviewsEmptyNode.hidden = true;

        for (const review of reviews) {
            const card = document.createElement('article');
            card.className = 'review-card';
            card.dataset.reviewId = String(review.id);

            card.innerHTML = `
                <p class="review-rating">Оценка: ${review.rating}/5</p>
                <p class="review-text">${escapeHtml(review.text)}</p>
                <p class="order-meta">${escapeHtml(review.created_at_display)} ${review.is_published ? '• опубликован' : '• на модерации'}</p>
                <button type="button" class="remove-link" data-action="delete-review">Удалить отзыв</button>
            `;

            reviewsNode.appendChild(card);
        }
    }

    async function loadProfile() {
        const data = await window.SiteApi.request('/api/profile/');
        const user = data.user || {};

        usernameNode.textContent = user.full_name || user.username || '';

        if (user.email) {
            emailWrapNode.hidden = false;
            emailNode.textContent = user.email;
        } else {
            emailWrapNode.hidden = true;
        }
    }

    async function loadOrders() {
        const data = await window.SiteApi.request('/api/profile/orders/');
        renderOrders(data.results || []);
    }

    async function loadReviews() {
        const data = await window.SiteApi.request('/api/profile/reviews/');
        renderReviews(data.results || []);
    }

    reviewsNode.addEventListener('click', async function (event) {
        const button = event.target.closest('button[data-action="delete-review"]');
        if (!button) {
            return;
        }

        const reviewCard = button.closest('[data-review-id]');
        if (!reviewCard) {
            return;
        }

        const reviewId = Number(reviewCard.dataset.reviewId);
        if (!reviewId) {
            return;
        }

        button.disabled = true;

        try {
            await window.SiteApi.request(`/api/profile/reviews/${reviewId}/`, {
                method: 'DELETE',
            });
            await loadReviews();
        } catch (error) {
            alert(error.message);
            button.disabled = false;
        }
    });

    (async function init() {
        try {
            await Promise.all([loadProfile(), loadOrders(), loadReviews()]);
        } catch (error) {
            alert(error.message);
        }
    })();
})();
