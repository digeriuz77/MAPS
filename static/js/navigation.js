/**
 * Role-Based Navigation Component
 * Dynamically updates navigation based on user's role
 */

/**
 * Update navigation bar based on user role
 * Hides Analysis and Reflection links for CONTROL users
 * Adds Logout button for authenticated users
 */
async function updateNavigationForRole() {
    try {
        const role = await getCachedUserRole();
        const navBar = document.querySelector('.nav-bar');
        
        if (!navBar) {
            console.warn('Navigation bar not found');
            return;
        }

        // Hide FULL-only links for CONTROL users
        if (role === 'CONTROL') {
            const analysisLink = navBar.querySelector('a[href="/analysis"]');
            const reflectionLink = navBar.querySelector('a[href="/reflection"]');
            // Note: Feedback is available to all users
            
            if (analysisLink) {
                analysisLink.style.display = 'none';
            }
            if (reflectionLink) {
                reflectionLink.style.display = 'none';
            }
        }

        // Add logout button if not already present
        const existingLogout = navBar.querySelector('.logout-btn');
        if (!existingLogout) {
            const logoutLink = document.createElement('a');
            logoutLink.href = '#';
            logoutLink.className = 'logout-btn';
            logoutLink.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
            logoutLink.onclick = async (e) => {
                e.preventDefault();
                await logout();
            };
            logoutLink.style.marginLeft = 'auto';
            navBar.appendChild(logoutLink);
        }

        console.log('✅ Navigation updated for role:', role);
    } catch (error) {
        console.error('Failed to update navigation:', error);
    }
}

/**
 * Initialize role-based navigation
 * Should be called when page loads
 */
async function initRoleBasedNavigation() {
    try {
        await initializeSupabase();
        const session = await requireAuth();
        
        if (session) {
            await updateNavigationForRole();
        }
    } catch (error) {
        console.error('Navigation initialization failed:', error);
        // requireAuth will handle redirect if not authenticated
    }
}

// Auto-initialize if navigation bar exists
document.addEventListener('DOMContentLoaded', async function() {
    const navBar = document.querySelector('.nav-bar');
    if (navBar && typeof initializeSupabase === 'function') {
        await initRoleBasedNavigation();
    }
});

window.updateNavigationForRole = updateNavigationForRole;
window.initRoleBasedNavigation = initRoleBasedNavigation;
