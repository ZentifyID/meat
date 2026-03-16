(function () {
    const filterForm = document.getElementById('products-filter-form');
    const listNode = document.getElementById('products-list');
    const emptyNode = document.getElementById('products-empty');
    const categorySelect = document.getElementById('products-category');
    const searchInput = document.getElementById('products-query');

    if (!filterForm || !listNode || !categorySelect || !searchInput) {
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

    function shortenText(value, maxLength) {
        const text = String(value || '');
        if (text.length <= maxLength) {
            return text;
        }
        return `${text.slice(0, maxLength - 1)}...`;
    }

    function renderProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';

        const availabilityClass = product.available ? 'available' : 'not-available';
        const availabilityText = product.available ? 'В наличии' : 'Нет в наличии';
        const safeName = escapeHtml(product.name);
        const safeDescription = escapeHtml(shortenText(product.description, 180));
        const safeCategoryName = escapeHtml(product.category.name);

        card.innerHTML = [
            product.image_url ? `<img src="${product.image_url}" alt="${safeName}">` : '',
            `<h3>${safeName}</h3>`,
            `<p>${safeDescription}</p>`,
            `<p><strong>Категория:</strong> ${safeCategoryName}</p>`,
            `<p class="price">${window.SiteApi.formatPrice(product.price)} ₽</p>`,
            `<p class="${availabilityClass}">${availabilityText}</p>`,
            product.available
                ? `<button class="btn" type="button" data-action="add" data-product-id="${product.id}">В корзину</button>`
                : '',
            `<a href="${product.detail_url}" class="btn">Подробнее</a>`,
        ].join('');

        return card;
    }

    async function loadCategories() {
        const data = await window.SiteApi.request('/api/categories/');
        const options = ['<option value="">Все категории</option>'];

        for (const category of data.results || []) {
            options.push(`<option value="${category.id}">${category.name}</option>`);
        }

        categorySelect.innerHTML = options.join('');

        const url = new URL(window.location.href);
        const selectedCategory = url.searchParams.get('category') || '';
        categorySelect.value = selectedCategory;
    }

    async function loadProducts() {
        const params = new URLSearchParams();
        const query = searchInput.value.trim();
        const category = categorySelect.value;

        if (query) {
            params.set('q', query);
        }
        if (category) {
            params.set('category', category);
        }

        const queryString = params.toString();
        const url = queryString ? `/api/products/?${queryString}` : '/api/products/';
        const data = await window.SiteApi.request(url);

        listNode.innerHTML = '';
        const products = data.results || [];

        if (!products.length) {
            emptyNode.hidden = false;
            return;
        }

        emptyNode.hidden = true;
        for (const product of products) {
            listNode.appendChild(renderProductCard(product));
        }

        const nextUrl = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname;
        window.history.replaceState({}, '', nextUrl);
    }

    async function addToCart(productId) {
        const data = await window.SiteApi.request('/api/cart/items/', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId, quantity: 1 }),
        });

        window.SiteApi.updateCartBadge(data.cart.total_count);
    }

    listNode.addEventListener('click', async function (event) {
        const button = event.target.closest('button[data-action="add"]');
        if (!button) {
            return;
        }

        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = 'Добавляем...';

        try {
            await addToCart(Number(button.dataset.productId));
            button.textContent = 'Добавлено';
            setTimeout(function () {
                button.textContent = originalText;
                button.disabled = false;
            }, 800);
        } catch (error) {
            alert(error.message);
            button.textContent = originalText;
            button.disabled = false;
        }
    });

    filterForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        try {
            await loadProducts();
        } catch (error) {
            alert(error.message);
        }
    });

    filterForm.addEventListener('reset', function () {
        setTimeout(function () {
            searchInput.value = '';
            categorySelect.value = '';
            loadProducts().catch(function (error) {
                alert(error.message);
            });
        }, 0);
    });

    (async function init() {
        const url = new URL(window.location.href);
        searchInput.value = url.searchParams.get('q') || '';

        try {
            await loadCategories();
            await loadProducts();
        } catch (error) {
            alert(error.message);
        }
    })();
})();
