(function () {
    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split('; ') : [];
        for (const cookie of cookies) {
            const [key, value] = cookie.split('=');
            if (key === name) {
                return decodeURIComponent(value || '');
            }
        }
        return '';
    }

    async function request(url, options) {
        const opts = options || {};
        const method = (opts.method || 'GET').toUpperCase();
        const headers = Object.assign({}, opts.headers || {});

        if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
            const csrftoken = getCookie('csrftoken');
            if (csrftoken) {
                headers['X-CSRFToken'] = csrftoken;
            }
            if (!headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }
        }

        const response = await fetch(url, {
            method,
            headers,
            body: opts.body,
            credentials: 'same-origin',
        });

        let data = null;
        try {
            data = await response.json();
        } catch (_error) {
            data = null;
        }

        if (!response.ok) {
            const message = data && data.error ? data.error : 'API request failed';
            const error = new Error(message);
            error.data = data;
            throw error;
        }

        return data;
    }

    function formatPrice(value) {
        const number = Number(value || 0);
        return new Intl.NumberFormat('ru-RU', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
        }).format(number);
    }

    function updateCartBadge(count) {
        const cartIcon = document.querySelector('.cart-icon');
        if (!cartIcon) {
            return;
        }

        let badge = document.getElementById('cart-count-badge');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.id = 'cart-count-badge';
                badge.className = 'cart-count';
                cartIcon.appendChild(badge);
            }
            badge.textContent = String(count);
            return;
        }

        if (badge) {
            badge.remove();
        }
    }

    window.SiteApi = {
        request,
        formatPrice,
        updateCartBadge,
    };
})();
