(function () {
    const form = document.getElementById('register-form');
    const errorNode = document.getElementById('register-error');

    if (!form || !errorNode || !window.SiteApi) {
        return;
    }

    function getErrorMessage(error) {
        if (error && error.data && error.data.errors) {
            const lines = [];
            for (const [field, messages] of Object.entries(error.data.errors)) {
                const text = Array.isArray(messages) ? messages.join(', ') : String(messages);
                lines.push(`${field}: ${text}`);
            }
            if (lines.length) {
                return lines.join(' | ');
            }
        }

        return (error && error.message) || 'Не удалось зарегистрироваться';
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        errorNode.hidden = true;

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const response = await window.SiteApi.request('/api/auth/register/', {
                method: 'POST',
                body: JSON.stringify({
                    username: form.username.value.trim(),
                    email: form.email.value.trim(),
                    password1: form.password1.value,
                    password2: form.password2.value,
                }),
            });

            window.location.href = response.redirect_url || '/profile/';
        } catch (error) {
            errorNode.textContent = getErrorMessage(error);
            errorNode.hidden = false;
            submitButton.disabled = false;
        }
    });
})();
