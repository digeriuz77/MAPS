/**
 * Auth Blocker - Prevents page content from showing until auth verified
 * This script runs IMMEDIATELY and blocks page rendering
 * Include this FIRST in <head> before any other scripts
 */

// Hide body immediately
document.documentElement.style.visibility = 'hidden';
document.documentElement.style.opacity = '0';

// Add loading overlay
const style = document.createElement('style');
style.textContent = `
    .auth-checking-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, #b2d8d8 0%, #66b2b2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999999;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .auth-checking-content {
        text-align: center;
        color: #004c4c;
    }
    .auth-spinner {
        border: 4px solid #b2d8d8;
        border-top: 4px solid #008080;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Create overlay
const overlay = document.createElement('div');
overlay.className = 'auth-checking-overlay';
overlay.innerHTML = `
    <div class="auth-checking-content">
        <div class="auth-spinner"></div>
        <h2>Verifying authentication...</h2>
        <p>Please wait</p>
    </div>
`;

// Add overlay as soon as possible
if (document.body) {
    document.body.appendChild(overlay);
} else {
    document.addEventListener('DOMContentLoaded', () => {
        document.body.appendChild(overlay);
    });
}

/**
 * Show page content after auth verified
 */
window.authCheckComplete = function() {
    // Remove overlay
    const authOverlay = document.querySelector('.auth-checking-overlay');
    if (authOverlay) {
        authOverlay.remove();
    }
    
    // Show page
    document.documentElement.style.visibility = 'visible';
    document.documentElement.style.opacity = '1';
    
    console.log('✅ Auth check complete, page visible');
};

/**
 * Redirect immediately on auth failure (before page shows)
 */
window.authCheckFailed = function(redirectUrl) {
    console.log(`❌ Auth check failed, redirecting to ${redirectUrl}`);
    window.location.replace(redirectUrl);
};
