/**
 * Auth Guard Functions - DISABLED
 * All auth checks removed - app is fully public
 * Functions are kept for backwards compatibility but do nothing
 */

/**
 * Check if user is authenticated - DISABLED
 * Always returns a mock session
 */
async function requireAuth() {
    console.log('ℹ️ Auth check skipped (auth disabled)');
    return { user: { id: 'anonymous', email: 'anonymous@example.com' } };
}

/**
 * Get user's role - DISABLED
 * Always returns 'FULL'
 */
async function getUserRole(userId) {
    return 'FULL';
}

/**
 * Require FULL access role - DISABLED
 * Always passes
 */
async function requireFullAccess() {
    return { user: { id: 'anonymous', email: 'anonymous@example.com' } };
}

/**
 * Get cached user role - DISABLED
 * Always returns 'FULL'
 */
async function getCachedUserRole() {
    return 'FULL';
}

/**
 * Log out current user - DISABLED
 * Just redirects to home
 */
async function logout() {
    window.location.href = '/';
}

/**
 * Check if current route is accessible - DISABLED
 * Always returns true
 */
async function canAccessRoute(route) {
    return true;
}

/**
 * Make API request - simple fetch wrapper
 * No authentication headers added
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Response>} Fetch response
 */
async function authenticatedFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    console.log(`📡 Fetch: ${options.method || 'GET'} ${url}`);

    return fetch(url, {
        ...options,
        headers
    });
}

// Export functions to window for global access
window.requireAuth = requireAuth;
window.getUserRole = getUserRole;
window.requireFullAccess = requireFullAccess;
window.getCachedUserRole = getCachedUserRole;
window.logout = logout;
window.canAccessRoute = canAccessRoute;
window.authenticatedFetch = authenticatedFetch;

console.log('✅ Auth guard loaded (auth disabled - all routes public)');
