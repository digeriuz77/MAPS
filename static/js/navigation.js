/**
 * Unified Navigation Loader Component
 * Dynamically loads navigation component into pages
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

            console.log('✅ Navigation loaded successfully');
        }
    } catch (error) {
        console.error('Failed to load navigation:', error);
    }
}

// Auto-initialize navigation on DOMContentLoaded
document.addEventListener('DOMContentLoaded', async function () {
    const container = document.getElementById('navigation-container');
    if (container) {
        await loadNavigation();
    }
});

window.loadNavigation = loadNavigation;
