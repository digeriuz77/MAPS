/**
 * MI Practice Main Application
 * Handles all MI Practice module functionality
 */

(function () {
    'use strict';

    // ============================================
    // STATE MANAGEMENT
    // ============================================

    const state = {
        currentUser: null,
        modules: [],
        learningPaths: [],
        currentAttempt: null,
        currentModule: null,
        userProgress: null,
        filters: {
            focusArea: '',
            difficulty: '',
            search: '',
            contentType: 'all'  // Filter by content type: shared, customer_facing, colleague_facing
        }
    };

    // ============================================
    // API CLIENT
    // ============================================

    const MIAPI = {
        baseUrl: '/api/mi-practice',

        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return response.json();
        },

        // Modules
        async listModules(filters = {}) {
            const params = new URLSearchParams();
            if (filters.focusArea) params.append('focus_area', filters.focusArea);
            if (filters.difficulty) params.append('difficulty', filters.difficulty);
            if (filters.contentType && filters.contentType !== 'all') params.append('content_type', filters.contentType);
            // user_id is optional - backend handles anonymous mode

            return this.request(`/modules?${params}`);
        },

        async getModule(moduleId) {
            // user_id is optional - backend handles anonymous mode
            return this.request(`/modules/${moduleId}`);
        },

        // Attempts
        async startAttempt(moduleId) {
            return this.request(`/modules/${moduleId}/start`, {
                method: 'POST',
                body: JSON.stringify({
                    module_id: moduleId
                    // user_id is handled by backend (anonymous mode)
                })
            });
        },

        async makeChoice(attemptId, choicePointId) {
            return this.request(`/attempts/${attemptId}/choose`, {
                method: 'POST',
                body: JSON.stringify({ choice_point_id: choicePointId })
            });
        },

        async getAttemptState(attemptId) {
            return this.request(`/attempts/${attemptId}/state`);
        },

        async completeAttempt(attemptId) {
            return this.request(`/attempts/${attemptId}/complete`, {
                method: 'POST'
            });
        },

        // Progress
        async getUserProgress(userId = null) {
            // userId is optional - backend handles anonymous mode
            const query = userId ? `?user_id=${userId}` : '';
            return this.request(`/progress${query}`);
        },

        async getCompetencyBreakdown(userId = null) {
            // userId is optional - backend handles anonymous mode
            const query = userId ? `?user_id=${userId}` : '';
            return this.request(`/progress/competencies${query}`);
        },

        // Learning Paths
        async listLearningPaths() {
            // user_id is optional - backend handles anonymous mode
            return this.request(`/learning-paths`);
        },

        async enrollInPath(pathId) {
            return this.request(`/learning-paths/${pathId}/enroll`, {
                method: 'POST',
                body: JSON.stringify({ path_id: pathId })
            });
        }
    };

    // ============================================
    // LANDING PAGE FUNCTIONS
    // ============================================

    async function initLandingPage() {
        try {
            // No authentication required - user is anonymous
            // Backend handles anonymous user ID normalization
            state.currentUser = null;

            // Load all data in parallel
            await Promise.all([
                loadLearningPaths(),
                loadModules(),
            ]);

            // Setup filters
            setupFilters();
            setupModuleTypeTabs();

            console.log('✅ MI Practice landing page initialized');
        } catch (error) {
            console.error('Failed to initialize landing page:', error);
            showError('Failed to load content. Please refresh the page.');
        }
    }

    async function loadHeroStats() {
        // Progress is available even without auth - backend handles anonymous mode

        try {
            const progress = await MIAPI.getUserProgress();

            document.getElementById('stat-modules-completed').textContent = progress.modules_completed || 0;
            document.getElementById('stat-practice-minutes').textContent = progress.total_practice_minutes || 0;

            const avgScore = calculateAverageCompetencyScore(progress.competency_scores);
            document.getElementById('stat-competency-score').textContent = avgScore > 0 ? avgScore.toFixed(1) : '-';
        } catch (error) {
            console.error('Failed to load hero stats:', error);
        }
    }

    async function loadLearningPaths() {
        const container = document.getElementById('learning-paths-container');
        if (!container) return;

        try {
            const paths = await MIAPI.listLearningPaths();
            state.learningPaths = paths;

            if (paths.length === 0) {
                MIComponents.showEmpty(container, 'No learning paths available yet', 'fa-route');
                return;
            }

            container.innerHTML = '';
            paths.forEach(path => {
                const card = MIComponents.createPathCard(path, {
                    onAction: (p) => handlePathAction(p)
                });
                container.appendChild(card);
            });
        } catch (error) {
            console.error('Failed to load learning paths:', error);
            MIComponents.showError(container, 'Failed to load learning paths', () => loadLearningPaths());
        }
    }

    async function loadModules() {
        const container = document.getElementById('modules-container');
        if (!container) return;

        try {
            const modules = await MIAPI.listModules(state.filters);
            state.modules = modules;
            renderModules(modules);
        } catch (error) {
            console.error('Failed to load modules:', error);
            MIComponents.showError(container, 'Failed to load modules', () => loadModules());
        }
    }

    function renderModules(modules) {
        const container = document.getElementById('modules-container');
        if (!container) return;

        if (modules.length === 0) {
            MIComponents.showEmpty(container, 'No modules match your filters', 'fa-search');
            return;
        }

        container.innerHTML = '';
        modules.forEach(module => {
            const card = MIComponents.createModuleCard(module, {
                onStart: (m) => startModule(m.id)
            });
            container.appendChild(card);
        });
    }

    // ============================================
    // CONTENT TYPE FILTERING
    // ============================================

    function setupModuleTypeTabs() {
        const tabs = document.querySelectorAll('.module-type-tabs .tab-btn');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });

                // Add active class to clicked tab
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');

                // Update filter and reload modules
                state.filters.contentType = tab.getAttribute('data-content-type');
                loadModules();
            });
        });
    }

    // ============================================
    // FILTERS
    // ============================================

    function setupFilters() {
        const focusSelect = document.getElementById('filter-focus');
        const difficultySelect = document.getElementById('filter-difficulty');
        const searchInput = document.getElementById('filter-search');

        if (focusSelect) {
            focusSelect.addEventListener('change', (e) => {
                state.filters.focusArea = e.target.value;
                loadModules();
            });
        }

        if (difficultySelect) {
            difficultySelect.addEventListener('change', (e) => {
                state.filters.difficulty = e.target.value;
                loadModules();
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', debounce((e) => {
                state.filters.search = e.target.value.toLowerCase();
                filterModulesBySearch();
            }, 300));
        }
    }

    function filterModulesBySearch() {
        const searchTerm = state.filters.search;
        if (!searchTerm) {
            renderModules(state.modules);
            return;
        }

        const filtered = state.modules.filter(m =>
            m.title.toLowerCase().includes(searchTerm) ||
            m.learning_objective?.toLowerCase().includes(searchTerm) ||
            m.mi_focus_area?.toLowerCase().includes(searchTerm) ||
            (m.maps_rubric?.target_competencies || []).some(c => c.toLowerCase().includes(searchTerm))
        );
        renderModules(filtered);
    }

    // ============================================
    // PROGRESS
    // ============================================

    async function loadProgressOverview() {
        const container = document.getElementById('progress-container');
        if (!container) return;

        try {
            // Progress is available even without auth - backend handles anonymous mode
            const progress = await MIAPI.getUserProgress();
            state.userProgress = progress;

            // Create a summary card
            const totalModules = state.modules.length || 1;
            const percentComplete = Math.round((progress.modules_completed / totalModules) * 100);

            container.innerHTML = `
                <div class="progress-summary-card">
                    <div class="progress-ring-container">
                        <svg class="progress-ring" viewBox="0 0 100 100" role="img" aria-label="Progress: ${percentComplete}%">
                            <circle class="progress-ring-bg" cx="50" cy="50" r="45"/>
                            <circle class="progress-ring-fill" cx="50" cy="50" r="45" 
                                    stroke-dasharray="${percentComplete * 2.83} 283"/>
                        </svg>
                        <span class="progress-percent">${percentComplete}%</span>
                    </div>
                    <div class="progress-details">
                        <h3>Overall Progress</h3>
                        <p>You have completed <strong>${progress.modules_completed}</strong> of <strong>${totalModules}</strong> modules</p>
                        <div class="progress-stats-row">
                            <span><i class="fas fa-check-circle"></i> ${progress.modules_completed} completed</span>
                            <span><i class="fas fa-play-circle"></i> ${progress.modules_attempted} attempted</span>
                        </div>
                        <div class="maps-progress-info">
                            <i class="fas fa-certificate" aria-hidden="true"></i>
                            <span>Building MaPS competencies through practice</span>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load progress overview:', error);
            container.innerHTML = '<p class="error-text">Unable to load progress</p>';
        }
    }

    // ============================================
    // MODULE ACTIONS
    // ============================================

    async function startModule(moduleId) {
        try {
            const attempt = await MIAPI.startAttempt(moduleId);
            window.location.href = `/mi-practice-module.html?attempt=${attempt.id}`;
        } catch (error) {
            console.error('Failed to start module:', error);
            showError('Failed to start module. Please try again.');
        }
    }

    async function handlePathAction(path) {
        if (path.is_enrolled) {
            // Continue the path
            const nextModule = path.next_module_id || path.modules?.[0]?.id;
            if (nextModule) {
                startModule(nextModule);
            }
        } else {
            // Enroll in the path
            try {
                await MIAPI.enrollInPath(path.id);
                showNotification(`Enrolled in ${path.title}`, 'success');
                loadLearningPaths();
            } catch (error) {
                console.error('Failed to enroll in path:', error);
                showError('Failed to enroll. Please try again.');
            }
        }
    }

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================

    function calculateAverageCompetencyScore(competencyScores) {
        if (!competencyScores || Object.keys(competencyScores).length === 0) return 0;
        const scores = Object.values(competencyScores);
        return scores.reduce((a, b) => a + b, 0) / scores.length;
    }

    function showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a proper notification system
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}" aria-hidden="true"></i>
            <span>${MIComponents.escapeHtml(message)}</span>
        `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function showError(message) {
        const container = document.querySelector('.mi-practice-container');
        if (container) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-banner';
            errorDiv.setAttribute('role', 'alert');
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
                <span>${MIComponents.escapeHtml(message)}</span>
                <button class="close-btn"><i class="fas fa-times" aria-hidden="true"></i></button>
            `;
            container.insertBefore(errorDiv, container.firstChild);

            errorDiv.querySelector('.close-btn').addEventListener('click', () => {
                errorDiv.remove();
            });
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ============================================
    // SESSION PAGE FUNCTIONS
    // ============================================

    async function initSessionPage() {
        /**
         * Initialize the MI Practice session page.
         * Called from mi-practice-module.html when starting a practice session.
         */
        try {
            // Get attempt_id from URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const attemptId = urlParams.get('attempt');

            if (!attemptId) {
                showError('No attempt ID provided. Please start a module from the main page.');
                return;
            }

            console.log(`Initializing session page for attempt: ${attemptId}`);

            // Load attempt state
            const state = await MIPracticeApp.getAttemptState(attemptId);
            if (!state) {
                showError('Failed to load attempt. Please try again.');
                return;
            }

            // Update UI with current state
            MIPracticeApp.renderSessionState(state);

            // Setup event listeners
            MIPracticeApp.setupSessionEventListeners(attemptId);

        } catch (error) {
            console.error('Failed to initialize session page:', error);
            showError('Failed to initialize practice session. Please refresh the page.');
        }
    }

    async function getAttemptState(attemptId) {
        const response = await MIAPI.getAttemptState(attemptId);
        return response;
    }

    function renderSessionState(state) {
        // Update header info
        const moduleInfo = state.current || {};
        document.getElementById('module-title').textContent = moduleInfo.module_title || 'Practice Session';
        document.getElementById('module-focus').textContent = moduleInfo.mi_focus_area || '';

        // Update metrics
        const metrics = state.state || {};
        if (metrics.rapport_score !== undefined) {
            MIPracticeApp.updateMetricBar('rapport', metrics.rapport_score);
        }
        if (metrics.resistance_level !== undefined) {
            MIPracticeApp.updateMetricBar('resistance', 10 - metrics.resistance_level); // Invert: lower resistance = better
        }
        document.getElementById('turn-count').textContent = metrics.turns_taken || 0;

        // Update persona card
        document.getElementById('persona-text').textContent = moduleInfo.persona_text || 'Loading...';
        document.getElementById('persona-mood').textContent = moduleInfo.persona_mood || '';

        // Render choice points
        const choices = state.choice_points || [];
        const container = document.getElementById('choices-container');
        if (choices.length === 0) {
            container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><span>Loading choices...</span></div>';
        } else {
            container.innerHTML = '';
            choices.forEach(choice => {
                const choiceCard = MIPracticeApp.createChoiceCard(choice);
                container.appendChild(choiceCard);
            });
        }
    }

    function updateMetricBar(metricType, value) {
        const fill = document.getElementById(`${metricType}-fill`);
        if (fill && value !== undefined) {
            const percentage = Math.max(0, Math.min(100, (value / 10) * 100));
            fill.style.width = `${percentage}%`;
        }
    }

    function createChoiceCard(choice) {
        const card = document.createElement('div');
        card.className = 'choice-card';
        card.setAttribute('data-choice-id', choice.id);

        const optionText = document.createElement('div');
        optionText.className = 'choice-text';
        optionText.textContent = choice.option_text;

        const previewHint = document.createElement('div');
        previewHint.className = 'choice-hint';
        previewHint.textContent = choice.preview_hint || '';

        card.appendChild(optionText);
        card.appendChild(previewHint);

        card.addEventListener('click', () => MIPracticeApp.selectChoice(choice.id));

        return card;
    }

    async function selectChoice(choicePointId) {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const attemptId = urlParams.get('attempt');

            const response = await MIAPI.makeChoice(attemptId, choicePointId);

            if (response.is_complete) {
                // Session complete - show completion
                MIPracticeApp.showCompletion(response);
            } else {
                // Update with new state
                MIPracticeApp.renderSessionState(response.new_state);
            }
        } catch (error) {
            console.error('Failed to select choice:', error);
            showError('Failed to process choice. Please try again.');
        }
    }

    function setupSessionEventListeners(attemptId) {
        // Exit button
        document.getElementById('btn-exit').addEventListener('click', () => {
            window.location.href = '/mi-practice.html';
        });

        // Hint button (placeholder)
        document.getElementById('btn-hint').addEventListener('click', () => {
            showNotification('Hint feature coming soon!', 'info');
        });

        // Skip button (placeholder)
        document.getElementById('btn-skip').addEventListener('click', () => {
            window.location.href = '/mi-practice.html';
        });
    }

    function showCompletion(result) {
        const container = document.querySelector('.mi-session-container');
        if (!container) return;

        container.innerHTML = `
            <div class="completion-screen" role="alert" aria-live="polite">
                <div class="completion-icon">
                    <i class="fas fa-check-circle fa-3x"></i>
                </div>
                <h1>Session Complete!</h1>
                <p>Great job practicing your MI skills.</p>
                <div class="completion-summary">
                    <p>Turns taken: ${result.turn_number || 0}</p>
                    <p>Final rapport: ${result.new_state?.rapport_score || 'N/A'}</p>
                </div>
                <a href="/mi-practice.html" class="btn-teal">Back to Modules</a>
            </div>
        `;
    }

    // ============================================
    // EXPORT
    // ============================================

    window.MIPracticeApp = {
        initLandingPage,
        initSessionPage
    };

})();
