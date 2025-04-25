document.addEventListener('DOMContentLoaded', () => {
    const userSelect = document.getElementById('user-select');
    // --- Removed radio button selection ---
    // const preferenceRadios = document.querySelectorAll('input[name="preference"]');
    const preferenceButtonsContainer = document.getElementById('preference-buttons'); // Get the button group container
    const calendarContainer = document.getElementById('calendar-container');
    const messageArea = document.getElementById('message-area');

    let selectedUser = userSelect.value || ''; // Initialize with current value if any
    let selectedPreference = ''; // Initialize preference

    userSelect.addEventListener('change', (event) => {
        selectedUser = event.target.value;
        clearMessage(); // Clear message on user change
    });

    // --- Removed radio button event listeners ---
    // preferenceRadios.forEach(radio => { ... });

    // --- New Event Listener for Preference Button Group ---
    if (preferenceButtonsContainer) {
        preferenceButtonsContainer.addEventListener('click', (event) => {
            // Check if a preference button was clicked
            if (event.target.classList.contains('pref-button')) {
                const clickedButton = event.target;
                const preferenceValue = clickedButton.dataset.preference;

                // If the clicked button is already active, do nothing
                // Alternatively, uncomment below to allow deselecting by clicking active button
                // if (clickedButton.classList.contains('active')) {
                //     clickedButton.classList.remove('active');
                //     selectedPreference = '';
                //     clearMessage();
                //     return;
                // }

                // Remove 'active' class from all buttons in the group
                preferenceButtonsContainer.querySelectorAll('.pref-button').forEach(button => {
                    button.classList.remove('active');
                });

                // Add 'active' class to the clicked button
                clickedButton.classList.add('active');

                // Update the selected preference state
                selectedPreference = preferenceValue;
                clearMessage(); // Clear message on preference change
            }
        });
    }
    // --- End New Event Listener ---


    calendarContainer.addEventListener('click', async (event) => {
        const dayElement = event.target.closest('.day:not(.empty)'); // Use closest to handle clicks on indicators too

        // Check if a valid day element was clicked
        if (dayElement) {
            const eventDate = dayElement.dataset.date;

            // Validate selection
            if (!selectedUser) {
                showMessage('Please select your name first.', 'error');
                return;
            }
            // Check the selectedPreference variable directly
            if (!selectedPreference) {
                showMessage('Please select a preference (Prefer Not, No, or Clear).', 'error');
                return;
            }

            showMessage('Updating...', 'info'); // Indicate processing

            const dataToSend = {
                user_name: selectedUser,
                event_date: eventDate,
                preference_type: selectedPreference // Use the variable
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
                    showMessage(result.message || `Preference set for ${eventDate}`, 'success');
                    // Update visual state of the clicked day
                    updateDayVisualState(dayElement, selectedUser, selectedPreference);
                } else {
                     // Handle potential JSON error response structure from Flask
                     let errorMsg = 'Failed to update preference.';
                     if (result && result.message) {
                         errorMsg = result.message;
                     } else if (!response.ok) {
                         errorMsg = `Error: ${response.status} - ${response.statusText}`;
                     }
                     showMessage(errorMsg, 'error');
                }

            } catch (error) {
                console.error('Error updating preference:', error);
                showMessage('An network or server error occurred. Please try again.', 'error');
            }
        }
    });

    function updateDayVisualState(dayElement, userName, preferenceType) {
        const userKey = userName.toLowerCase();
        const indicatorContainer = dayElement.querySelector('.indicators');
        if (!indicatorContainer) {
             console.error("Could not find indicator container for day:", dayElement.dataset.date);
             return;
         } // Should exist based on template

         // Remove existing indicator for this user
        const existingIndicator = indicatorContainer.querySelector(`.indicator.${userKey}`);
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Remove or Update data attribute
        if (preferenceType === 'clear') {
            delete dayElement.dataset[userKey]; // Remove attribute like 'data-jack'
        } else {
             dayElement.dataset[userKey] = preferenceType; // Set attribute like data-jack="no"

            // Add new indicator span only if not 'clear'
            const newIndicator = document.createElement('span');
            newIndicator.classList.add('indicator', userKey, preferenceType);
            newIndicator.textContent = userName[0]; // First initial
            indicatorContainer.appendChild(newIndicator);

            // Reset specific styles potentially overridden by classes (like Nick's color)
            newIndicator.style.color = ''; // Clear inline style if any
            if (userKey === 'nick' && (preferenceType === 'prefer_not' || preferenceType === 'no')) {
                 // Re-apply dark text for yellow background if needed based on CSS classes
                 // Note: This might be better handled solely by CSS if possible.
                 // Example: .indicator.nick.prefer_not, .indicator.nick.no { color: #333 !important; }
                 // If CSS handles it, this JS part might not be needed. Check style.css.
                 // For now, keep it for robustness:
                  if (window.getComputedStyle(newIndicator).backgroundColor === 'rgb(255, 193, 7)') { // Check if bg is yellow
                      newIndicator.style.color = '#333';
                  }
            }
        }
    }

    function showMessage(message, type = 'info') {
        messageArea.textContent = message;
        // Apply class to the container itself for styling
        messageArea.className = `message-area ${type}`; // 'success', 'error', 'info'

         // Optional: Clear message after a few seconds
         // Avoid clearing info messages too quickly
         if (type === 'success' || type === 'error') {
             setTimeout(clearMessage, 4000);
         }
    }

     function clearMessage() {
         messageArea.textContent = '';
         messageArea.className = 'message-area'; // Reset class
     }

});