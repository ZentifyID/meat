(function () {
    const form = document.getElementById('login-form');
    const errorNode = document.getElementById('login-error');

    if (!form || !errorNode || !window.SiteApi) {
        return;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        errorNode.hidden = true;

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const response = await window.SiteApi.request('/api/auth/login/', {
                method: 'POST',
                body: JSON.stringify({
                    username: form.username.value.trim(),
                    password: form.password.value,
                }),
            });

            window.location.href = response.redirect_url || '/profile/';
        } catch (error) {
            errorNode.textContent = error.message || 'Не удалось выполнить вход';
            errorNode.hidden = false;
            submitButton.disabled = false;
        }
    });
})();
