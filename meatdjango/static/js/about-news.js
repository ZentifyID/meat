(function () {
    const listNode = document.getElementById('about-news-list');
    const emptyNode = document.getElementById('about-news-empty');
    const errorNode = document.getElementById('about-news-error');

    if (!listNode || !emptyNode || !errorNode) {
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

    function renderNews(newsItems) {
        listNode.innerHTML = '';

        if (!newsItems.length) {
            emptyNode.hidden = false;
            return;
        }

        emptyNode.hidden = true;

        for (const item of newsItems) {
            const card = document.createElement('article');
            card.className = 'news-card';

            card.innerHTML = `
                ${item.image_url ? `<img src="${item.image_url}" alt="${escapeHtml(item.title)}" class="news-image">` : ''}
                <h4>${escapeHtml(item.title)}</h4>
                <p>${escapeHtml(item.preview_text)}</p>
                <p class="news-date">${escapeHtml(item.published_at_display)}</p>
                <a href="${item.detail_url}" class="btn news-read-more">Читать полностью</a>
            `;

            listNode.appendChild(card);
        }
    }

    async function loadNews() {
        const data = await window.SiteApi.request('/api/news/?limit=12');
        renderNews(data.results || []);
        errorNode.hidden = true;
    }

    loadNews().catch(function (error) {
        errorNode.textContent = error.message || 'Не удалось загрузить новости.';
        errorNode.hidden = false;
    });
})();
