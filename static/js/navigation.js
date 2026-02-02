/**
 * Unified Navigation Loader and Role-Based Navigation Component
 * Dynamically loads navigation and updates based on user's role
 */

/**
 * Load the unified navigation component into the page
 * @returns {Promise<void>}
 */
async function loadNavigation() {
    const container = document.getElementById('navigation-container');
    if (!container) {
        console.warn('Navigation container not found');
        return;
    }

    try {
        const response = await fetch('/static/components/navigation.html');
        if (!response.ok) throw new Error('Failed to load navigation');

        const html = await response.text();

        // Parse the HTML to extract just the nav content (not the full HTML document)
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Get nav element, style, and script
        const nav = doc.querySelector('nav');
        const styles = doc.querySelectorAll('style');
        const scripts = doc.querySelectorAll('script');

        if (nav) {
            container.innerHTML = '';
            container.appendChild(nav.cloneNode(true));

            // Append styles
            styles.forEach(style => {
                if (!document.querySelector(`style[data-nav-style]`)) {
                    const styleEl = style.cloneNode(true);
                    styleEl.setAttribute('data-nav-style', 'true');
                    document.head.appendChild(styleEl);
                }
            });

            // Execute scripts
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.textContent = script.textContent;
                document.body.appendChild(newScript);
            });

            // Update navigation for user role
            await updateNavigationForRole();
        }
    } catch (error) {
        console.error('Failed to load navigation:', error);
    }
}

/**
 * Update navigation bar based on user role
 * Hides Analysis and Reflection links for CONTROL users
 * Adds Logout button for authenticated users
 */
async function updateNavigationForRole() {
    try {
        const role = await getCachedUserRole();
        const navBar = document.querySelector('.unified-nav, .nav-bar');

        if (!navBar) {
            console.warn('Navigation bar not found');
            return;
        }

        // Role-based filtering removed - all users have access to all features
        console.log('Role access check skipped - all features enabled');

        // Add logout button if not already present
        const existingLogout = navBar.querySelector('.logout-btn');
        const navActions = navBar.querySelector('.nav-actions');

        if (!existingLogout && navActions) {
            const logoutBtn = document.createElement('button');
            logoutBtn.className = 'logout-btn';
            logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i>';
            logoutBtn.title = 'Logout';
            logoutBtn.style.cssText = `
                background: transparent;
                border: 2px solid #EF4444;
                color: #EF4444;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-left: 0.5rem;
            `;
            logoutBtn.onclick = async (e) => {
                e.preventDefault();
                await logout();
            };
            navActions.appendChild(logoutBtn);
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
document.addEventListener('DOMContentLoaded', async function () {
    const navBar = document.querySelector('.nav-bar');
    if (navBar && typeof initializeSupabase === 'function') {
        await initRoleBasedNavigation();
    }
});

window.updateNavigationForRole = updateNavigationForRole;
window.initRoleBasedNavigation = initRoleBasedNavigation;
window.loadNavigation = loadNavigation;
