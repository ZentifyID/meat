(function () {
    const button = document.getElementById('nav-logout-button');
    if (!button) {
        return;
    }

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

    fetch('/api/auth/session/', {
        method: 'GET',
        credentials: 'same-origin',
    }).catch(function () {
        return null;
    });

    button.addEventListener('click', async function () {
        button.disabled = true;

        try {
            const response = await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: '{}',
            });

            let data = {};
            try {
                data = await response.json();
            } catch (_error) {
                data = {};
            }

            if (!response.ok) {
                throw new Error(data.error || 'Не удалось выйти из аккаунта');
            }

            window.location.href = data.redirect_url || '/';
        } catch (error) {
            alert(error.message);
            button.disabled = false;
        }
    });
})();
