/**
 * Supabase Client Configuration
 * Provides authenticated access to Supabase for frontend
 */

// Initialize Supabase client
// In production, these should come from environment variables
// For now, we'll fetch them from the backend
let supabaseClient = null;

let initializationPromise = null;

async function initializeSupabase() {
    if (supabaseClient) {
        return supabaseClient;
    }

    // Return existing promise if initialization is already in progress
    if (initializationPromise) {
        return initializationPromise;
    }

    initializationPromise = (async () => {
        try {
            // Wait for Supabase SDK to load (with retry)
            let retries = 0;
            const maxRetries = 10;
            while (typeof window.supabase === 'undefined' && retries < maxRetries) {
                console.log(`Waiting for Supabase SDK to load... (attempt ${retries + 1}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 100));
                retries++;
            }

            if (typeof window.supabase === 'undefined') {
                throw new Error('Supabase SDK failed to load. Make sure the CDN script tag is present and network is accessible.');
            }

            // Fetch Supabase configuration from backend
            const response = await fetch('/api/config/supabase');
            if (!response.ok) {
                throw new Error(`Failed to fetch Supabase config: ${response.statusText}`);
            }
            const config = await response.json();

            // Initialize Supabase client using the global supabase object
            const { createClient } = window.supabase;
            supabaseClient = createClient(config.url, config.anonKey);

            console.log('✅ Supabase client initialized');
            return supabaseClient;
        } catch (error) {
            console.error('❌ Failed to initialize Supabase:', error);
            initializationPromise = null; // Reset promise on error so we can try again
            throw error;
        }
    })();

    return initializationPromise;
}

// Get current Supabase client
function getSupabaseClient() {
    if (!supabaseClient) {
        throw new Error('Supabase client not initialized. Call initializeSupabase() first.');
    }
    return supabaseClient;
}

// Export for use in other files
window.initializeSupabase = initializeSupabase;
window.getSupabaseClient = getSupabaseClient;
