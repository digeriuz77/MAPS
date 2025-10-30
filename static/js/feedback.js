/**
 * Feedback Form Handler
 * Handles feedback submission to the API
 */

// Initialize feedback page
document.addEventListener('DOMContentLoaded', function() {
    initializeFeedbackPage();
});

function initializeFeedbackPage() {
    const helpfulnessSlider = document.getElementById('helpfulness');
    const ratingValue = document.getElementById('ratingValue');
    const helpfulSection = document.getElementById('helpfulSection');
    const submitButton = document.getElementById('submitFeedback');

    // Update rating display
    helpfulnessSlider.addEventListener('input', function() {
        const value = this.value;
        ratingValue.textContent = value;
        
        // Show/hide "what was helpful" section
        if (value > 1) {
            helpfulSection.style.display = 'block';
        } else {
            helpfulSection.style.display = 'none';
        }
    });

    // Handle form submission
    submitButton.addEventListener('click', async function() {
        await submitFeedback();
    });

    console.log('✅ Feedback page initialized');
}

async function submitFeedback() {
    const helpfulnessScore = parseInt(document.getElementById('helpfulness').value);
    const whatHelpful = document.getElementById('whatHelpful').value.trim();
    const improvements = document.getElementById('improvements').value.trim();
    const submitButton = document.getElementById('submitFeedback');

    // Validation
    if (helpfulnessScore > 1 && !whatHelpful) {
        alert('Please tell us what you found helpful.');
        return;
    }

    // Get session information
    const sessionId = localStorage.getItem('currentSessionId') || 'feedback-' + Date.now();
    const conversationId = localStorage.getItem('currentConversationId') || null;
    const personaPracticed = localStorage.getItem('personaPracticed') || null;

    // Prepare feedback data
    const feedbackData = {
        session_id: sessionId,
        conversation_id: conversationId,
        persona_practiced: personaPracticed,
        helpfulness_score: helpfulnessScore,
        what_was_helpful: helpfulnessScore > 1 ? whatHelpful : null,
        improvement_suggestions: improvements || null,
        user_email: null // Optional: could prompt for email
    };

    console.log('Submitting feedback:', feedbackData);

    // Disable button during submission
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
        // Submit feedback (no authentication required)
        const response = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ Feedback submitted successfully:', result);

        // Show success message
        showSuccessMessage();

        // Clear form
        document.getElementById('helpfulness').value = 5;
        document.getElementById('ratingValue').textContent = '5';
        document.getElementById('whatHelpful').value = '';
        document.getElementById('improvements').value = '';
        document.getElementById('helpfulSection').style.display = 'none';

        // Enable next button
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.onclick = () => window.location.href = '/thank-you';
        }

    } catch (error) {
        console.error('❌ Failed to submit feedback:', error);
        alert(`Failed to submit feedback: ${error.message}\n\nPlease try again or contact support.`);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Feedback';
    }
}

function showSuccessMessage() {
    const container = document.querySelector('.feedback-container');
    
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <h3>Thank you for your feedback!</h3>
        <p>Your input helps us improve the platform.</p>
    `;
    successDiv.style.cssText = `
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
    `;
    
    container.insertBefore(successDiv, container.firstChild);
    
    // Remove after 5 seconds
    setTimeout(() => {
        successDiv.remove();
    }, 5000);
}
