(function () {
    const root = document.getElementById('news-detail-root');
    const titleNode = document.getElementById('news-detail-title');
    const breadcrumbNode = document.getElementById('news-detail-breadcrumb');
    const dateNode = document.getElementById('news-detail-date');
    const imageNode = document.getElementById('news-detail-image');
    const leadNode = document.getElementById('news-detail-lead');
    const contentNode = document.getElementById('news-detail-content');
    const errorNode = document.getElementById('news-detail-error');

    if (!root || !titleNode || !contentNode || !dateNode || !imageNode || !leadNode || !errorNode || !breadcrumbNode) {
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

    function formatContent(text) {
        const safe = escapeHtml(text || '');
        return safe.replaceAll('\n', '<br>');
    }

    function renderNews(news) {
        titleNode.textContent = news.title;
        breadcrumbNode.textContent = news.title;
        dateNode.textContent = news.published_at_display;

        if (news.image_url) {
            imageNode.src = news.image_url;
            imageNode.alt = news.title;
            imageNode.hidden = false;
        } else {
            imageNode.hidden = true;
            imageNode.removeAttribute('src');
        }

        if (news.short_description) {
            leadNode.textContent = news.short_description;
            leadNode.hidden = false;
        } else {
            leadNode.hidden = true;
            leadNode.textContent = '';
        }

        contentNode.innerHTML = formatContent(news.content);
        errorNode.hidden = true;

        document.title = `${news.title}`;
    }

    async function loadNewsDetail() {
        const newsId = Number(root.dataset.newsId);
        if (!newsId) {
            throw new Error('Некорректный идентификатор новости.');
        }

        const data = await window.SiteApi.request(`/api/news/${newsId}/`);
        renderNews(data.news);
    }

    loadNewsDetail().catch(function (error) {
        titleNode.textContent = 'Новость недоступна';
        contentNode.innerHTML = '';
        errorNode.textContent = error.message || 'Не удалось загрузить новость.';
        errorNode.hidden = false;
    });
})();
