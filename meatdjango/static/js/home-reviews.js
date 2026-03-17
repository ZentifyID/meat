(function () {
    const reviewsList = document.getElementById('home-reviews-list');
    const reviewsEmpty = document.getElementById('home-reviews-empty');
    const reviewForm = document.getElementById('home-review-form');
    const successNode = document.getElementById('reviews-success');
    const errorNode = document.getElementById('reviews-error');

    if (!reviewsList || !reviewsEmpty || !reviewForm || !successNode || !errorNode) {
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

    function renderReviews(reviews) {
        reviewsList.innerHTML = '';

        if (!reviews.length) {
            reviewsEmpty.hidden = false;
            return;
        }

        reviewsEmpty.hidden = true;

        for (const review of reviews) {
            const card = document.createElement('article');
            card.className = 'review-card';

            card.innerHTML = `
                <div class="review-meta">
                    <strong>${escapeHtml(review.name)}</strong>
                    ${review.city ? `<span>${escapeHtml(review.city)}</span>` : ''}
                </div>
                <p class="review-rating">Оценка: ${review.rating}/5</p>
                <p class="review-text">${escapeHtml(review.text)}</p>
            `;

            reviewsList.appendChild(card);
        }
    }

    async function loadReviews() {
        const data = await window.SiteApi.request('/api/reviews/');
        renderReviews(data.results || []);
    }

    function showSuccess(message) {
        successNode.textContent = message;
        successNode.hidden = false;
        errorNode.hidden = true;
    }

    function showError(message) {
        errorNode.textContent = message;
        errorNode.hidden = false;
        successNode.hidden = true;
    }

    function clearMessages() {
        successNode.hidden = true;
        errorNode.hidden = true;
    }

    function normalizeErrors(data) {
        if (!data) {
            return 'Не удалось отправить отзыв. Попробуйте снова.';
        }

        if (data.error) {
            return data.error;
        }

        if (data.errors) {
            const chunks = [];
            for (const [field, errors] of Object.entries(data.errors)) {
                const joined = Array.isArray(errors) ? errors.join(', ') : String(errors);
                chunks.push(`${field}: ${joined}`);
            }
            if (chunks.length) {
                return chunks.join(' | ');
            }
        }

        return 'Не удалось отправить отзыв. Проверьте поля формы.';
    }

    reviewForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        clearMessages();

        const payload = {
            name: reviewForm.name.value.trim(),
            city: reviewForm.city.value.trim(),
            rating: Number(reviewForm.rating.value),
            text: reviewForm.text.value.trim(),
        };

        const submitButton = reviewForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const response = await window.SiteApi.request('/api/reviews/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            showSuccess(response.message || 'Спасибо! Отзыв отправлен на модерацию.');
            reviewForm.text.value = '';
            reviewForm.rating.value = '5';
            await loadReviews();
        } catch (error) {
            const message = normalizeErrors(error && error.data ? error.data : { error: error.message });
            showError(message);
        } finally {
            submitButton.disabled = false;
        }
    });

    loadReviews().catch(function (error) {
        showError(error.message || 'Не удалось загрузить отзывы.');
    });
})();
