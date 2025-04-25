document.addEventListener('DOMContentLoaded', () => {
    const userSelect = document.getElementById('user-select');
    const preferenceRadios = document.querySelectorAll('input[name="preference"]');
    const calendarContainer = document.getElementById('calendar-container');
    const messageArea = document.getElementById('message-area');

    let selectedUser = '';
    let selectedPreference = '';

    userSelect.addEventListener('change', (event) => {
        selectedUser = event.target.value;
        // Maybe clear message on user change
        clearMessage(); 
    });

    preferenceRadios.forEach(radio => {
        radio.addEventListener('change', (event) => {
            if (event.target.checked) {
                selectedPreference = event.target.value;
                // Maybe clear message on preference change
                clearMessage(); 
            }
        });
    });

    calendarContainer.addEventListener('click', async (event) => {
        // Check if a day element was clicked (and not an empty one)
        if (event.target.classList.contains('day') && !event.target.classList.contains('empty')) {
            const dayElement = event.target;
            const eventDate = dayElement.dataset.date;

            // Validate selection
            if (!selectedUser) {
                showMessage('Please select your name first.', 'error');
                return;
            }
            if (!selectedPreference) {
                showMessage('Please select a preference (Prefer Not, No, or Clear).', 'error');
                return;
            }

            showMessage('Updating...', 'info'); // Indicate processing

            const dataToSend = {
                user_name: selectedUser,
                event_date: eventDate,
                preference_type: selectedPreference
            };

            try {
                const response = await fetch('/api/preferences', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(dataToSend),
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    showMessage(result.message, 'success');
                    // Update visual state of the clicked day
                    updateDayVisualState(dayElement, selectedUser, selectedPreference);
                } else {
                    showMessage(result.message || 'Failed to update preference.', 'error');
                }

            } catch (error) {
                console.error('Error updating preference:', error);
                showMessage('An error occurred. Please try again.', 'error');
            }
        }
    });

    function updateDayVisualState(dayElement, userName, preferenceType) {
        const userKey = userName.toLowerCase();
        const indicatorContainer = dayElement.querySelector('.indicators');
        if (!indicatorContainer) return; // Should exist based on template

         // Remove existing indicator for this user
        const existingIndicator = indicatorContainer.querySelector(`.indicator.${userKey}`);
        if (existingIndicator) {
            existingIndicator.remove();
        }

        if (preferenceType === 'clear') {
            // Remove the data attribute
            delete dayElement.dataset[userKey];
        } else {
             // Update the data attribute
            dayElement.dataset[userKey] = preferenceType;

            // Add new indicator span
            const newIndicator = document.createElement('span');
            newIndicator.classList.add('indicator', userKey, preferenceType);
            newIndicator.textContent = userName[0]; // First initial
            indicatorContainer.appendChild(newIndicator);
            
            // Special case for Nick's yellow background potentially needing dark text
            if (userKey === 'nick') {
                 newIndicator.style.color = '#333';
            }
        }
    }

    function showMessage(message, type = 'info') {
        messageArea.textContent = message;
        messageArea.className = type; // 'success', 'error', 'info'
         // Optional: Clear message after a few seconds
         setTimeout(clearMessage, 4000);
    }
     function clearMessage() {
         messageArea.textContent = '';
         messageArea.className = '';
     }

});