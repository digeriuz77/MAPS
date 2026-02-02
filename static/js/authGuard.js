/**
 * Authentication Guard Functions
 * Provides authentication and authorization checks for protected routes
 */

/**
 * Check if user is authenticated
 * Redirects to /auth if not authenticated
 * @returns {Promise<Object>} User session data
 */
async function requireAuth() {
    try {
        const supabase = window.getSupabaseClient();
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error || !session) {
            console.log('❌ No active session, redirecting to auth...');
            // Immediate redirect - don't wait
            window.location.replace('/auth');
            // Throw error to stop execution
            throw new Error('Not authenticated');
        }

        console.log('✅ User authenticated:', session.user.email);
        return session;
    } catch (error) {
        console.error('Auth check failed:', error);
        // Force redirect even on error
        window.location.replace('/auth');
        throw error;
    }
}

/**
 * Get user's role from profiles table
 * @param {string} userId - User ID from auth session
 * @returns {Promise<string>} User role ('FULL' or 'CONTROL')
 */
async function getUserRole(userId) {
    try {
        const supabase = window.getSupabaseClient();

        const { data, error } = await supabase
            .from('profiles')
            .select('role')
            .eq('id', userId)
            .single();

        if (error) {
            console.error('❌ Failed to fetch user role:', error);
            throw error;
        }

        if (!data) {
            console.error('❌ No profile found for user');
            throw new Error('Profile not found');
        }

        const role = data.role;
        console.log(`✅ User role: ${role}`);

        // Store role in localStorage for quick access
        localStorage.setItem('userRole', role);

        return role;
    } catch (error) {
        console.error('Error getting user role:', error);
        throw error;
    }
}

/**
 * Require FULL access role
 * Redirects CONTROL users to /thank-you-locked
 * @returns {Promise<Object>} Session data if user has FULL access
 */
/**
 * Require FULL access role - DEPRECATED
 * Now acts as a simple auth check since role restrictions are removed
 * @returns {Promise<Object>} Session data
 */
async function requireFullAccess() {
    // Simply check for authentication, ignore specific role
    const session = await requireAuth();
    console.log('✅ User authenticated (Full access check skipped)');
    return session;
}

/**
 * Get cached user role from localStorage
 * Falls back to fetching from Supabase if not cached
 * @returns {Promise<string>} User role
 */
async function getCachedUserRole() {
    const cachedRole = localStorage.getItem('userRole');

    if (cachedRole) {
        return cachedRole;
    }

    // If not cached, fetch from Supabase
    const session = await requireAuth();
    return await getUserRole(session.user.id);
}

/**
 * Log out current user
 * Clears session and redirects to /auth
 */
async function logout() {
    try {
        const supabase = window.getSupabaseClient();
        const { error } = await supabase.auth.signOut();

        if (error) {
            console.error('❌ Logout error:', error);
        }

        // Clear localStorage
        localStorage.removeItem('userRole');
        localStorage.clear();

        console.log('✅ User logged out');

        // Redirect to auth page
        window.location.href = '/auth';
    } catch (error) {
        console.error('Logout failed:', error);
        // Force redirect anyway
        window.location.href = '/auth';
    }
}

/**
 * Check if current route is accessible by user's role
 * @param {string} route - Route path to check
 * @returns {Promise<boolean>} True if accessible
 */
async function canAccessRoute(route) {
    // Role-based access control removed - all routes accessible
    return true;
}

/**
 * Make authenticated API request
 * Automatically includes the Bearer token from current session
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Response>} Fetch response
 */
async function authenticatedFetch(url, options = {}) {
    try {
        // Ensure Supabase is initialized before making authenticated requests
        const supabase = await window.initializeSupabase();
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error || !session) {
            throw new Error('No valid session for API request');
        }

        // Merge headers with authorization token
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
            ...options.headers
        };

        return fetch(url, {
            ...options,
            headers
        });
    } catch (error) {
        console.error('❌ Authenticated fetch failed:', error);
        throw error;
    }
}

// Export functions to window for global access
window.requireAuth = requireAuth;
window.getUserRole = getUserRole;
window.requireFullAccess = requireFullAccess;
window.getCachedUserRole = getCachedUserRole;
window.logout = logout;
window.canAccessRoute = canAccessRoute;
window.authenticatedFetch = authenticatedFetch;
