document.addEventListener('DOMContentLoaded', () => {
    const userButtonsContainer = document.getElementById('user-buttons');
    const preferenceButtonsContainer = document.getElementById('preference-buttons');
    const calendarContainer = document.getElementById('calendar-container');
    const messageArea = document.getElementById('message-area');

    // Auth UI
    const authStatus = document.getElementById('auth-status');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const passwordInput = document.getElementById('admin-password');

    let isAdmin = document.body.dataset.admin === '1';
    let selectedUser = '';
    let selectedPreference = '';

    updateAuthUI();

    async function refreshAuth() {
        try {
            const res = await fetch('/api/auth/status');
            const data = await res.json();
            isAdmin = !!data.is_admin;
            updateAuthUI();
        } catch (e) {
            // If status check fails, stay conservative: treat as locked
            isAdmin = false;
            updateAuthUI();
        }
    }

    function updateAuthUI() {
        if (isAdmin) {
            authStatus.textContent = 'Unlocked (edit mode)';
            if (loginForm) loginForm.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = '';
        } else {
            authStatus.textContent = 'Read-only (locked)';
            if (loginForm) loginForm.style.display = '';
            if (logoutBtn) logoutBtn.style.display = 'none';
        }
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const pwd = passwordInput.value || '';
            if (!pwd) {
                showMessage('Enter a password to unlock.', 'error');
                return;
            }
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: pwd })
                });
                const data = await res.json();
                if (res.ok) {
                    passwordInput.value = '';
                    showMessage(data.message || 'Unlocked.', 'success');
                    await refreshAuth();
                } else {
                    showMessage(data.message || 'Invalid password.', 'error');
                }
            } catch (err) {
                showMessage('Network error while unlocking.', 'error');
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/auth/logout', { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    showMessage(data.message || 'Locked.', 'success');
                    await refreshAuth();
                } else {
                    showMessage('Failed to lock.', 'error');
                }
            } catch (err) {
                showMessage('Network error while locking.', 'error');
            }
        });
    }

    if (userButtonsContainer) {
        userButtonsContainer.addEventListener('click', (event) => {
            const clickedButton = event.target.closest('.user-button');
            if (!clickedButton) return;

            if (!isAdmin) {
                showMessage('Read-only mode. Unlock to make changes.', 'error');
                return;
            }

            if (clickedButton.classList.contains('active')) return;

            userButtonsContainer.querySelectorAll('.user-button').forEach(btn => btn.classList.remove('active'));
            clickedButton.classList.add('active');

            selectedUser = clickedButton.dataset.user;
            clearMessage();
        });
    }

    if (preferenceButtonsContainer) {
        preferenceButtonsContainer.addEventListener('click', (event) => {
            const clickedButton = event.target.closest('.pref-button');
            if (!clickedButton) return;

            if (!isAdmin) {
                showMessage('Read-only mode. Unlock to make changes.', 'error');
                return;
            }

            if (clickedButton.classList.contains('active')) return;

            preferenceButtonsContainer.querySelectorAll('.pref-button').forEach(btn => btn.classList.remove('active'));
            clickedButton.classList.add('active');

            selectedPreference = clickedButton.dataset.preference;
            clearMessage();
        });
    }

    calendarContainer.addEventListener('click', async (event) => {
        const dayElement = event.target.closest('.day:not(.empty)');
        if (!dayElement) return;

        if (!isAdmin) {
            showMessage('Read-only mode. Unlock to make changes.', 'error');
            return;
        }

        const eventDate = dayElement.dataset.date;
        if (!selectedUser) {
            showMessage('Please select your name first.', 'error');
            return;
        }
        if (!selectedPreference) {
            showMessage('Please select a preference (Prefer Not, No, or Clear).', 'error');
            return;
        }

        showMessage('Updating...', 'info');

        const dataToSend = {
            user_name: selectedUser,
            event_date: eventDate,
            preference_type: selectedPreference
        };

        try {
            const response = await fetch('/api/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSend),
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                showMessage(result.message || `Preference set for ${eventDate}`, 'success');
                updateDayVisualState(dayElement, selectedUser, selectedPreference);
            } else {
                let errorMsg = result?.message || `Error: ${response.status} - ${response.statusText}`;
                showMessage(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Error updating preference:', error);
            showMessage('A network or server error occurred. Please try again.', 'error');
        }
    });

    function updateDayVisualState(dayElement, userName, preferenceType) {
        const userKey = userName.toLowerCase();
        const indicatorContainer = dayElement.querySelector('.indicators');
        if (!indicatorContainer) {
            console.error("Could not find indicator container for day:", dayElement.dataset.date);
            return;
        }

        const existingIndicator = indicatorContainer.querySelector(`.indicator.${userKey}`);
        if (existingIndicator) existingIndicator.remove();

        if (preferenceType === 'clear') {
            delete dayElement.dataset[userKey];
        } else {
            dayElement.dataset[userKey] = preferenceType;

            const newIndicator = document.createElement('span');
            newIndicator.classList.add('indicator', userKey, preferenceType);
            newIndicator.textContent = userName[0];
            indicatorContainer.appendChild(newIndicator);
        }
    }

    function showMessage(message, type = 'info') {
        messageArea.textContent = message;
        messageArea.className = `message-area ${type}`;
        if (type === 'success' || type === 'error') {
            setTimeout(clearMessage, 4000);
        }
    }

    function clearMessage() {
        messageArea.textContent = '';
        messageArea.className = 'message-area';
    }
});
