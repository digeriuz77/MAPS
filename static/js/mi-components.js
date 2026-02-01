/**
 * MI Practice Reusable UI Components
 * Provides component builders for the MI Practice module interface
 */

(function () {
    'use strict';

    // ============================================
    // COMPONENT BUILDERS
    // ============================================

    const MIComponents = {

        /**
         * Create a module card with MaPS framework alignment
         * @param {Object} module - Module data
         * @param {Object} options - Optional configuration
         * @returns {HTMLElement} Module card element
         */
        createModuleCard(module, options = {}) {
            const card = document.createElement('div');
            card.className = 'module-card';
            card.setAttribute('role', 'listitem');
            card.setAttribute('data-module-id', module.id);
            card.setAttribute('data-content-type', module.content_type || 'shared');

            const difficultyClass = `difficulty-${module.difficulty_level}`;
            const focusAreaIcon = this.getFocusAreaIcon(module.mi_focus_area);

            // Determine content type label and icon
            const contentType = module.content_type || 'shared';
            const contentTypeInfo = this.getContentTypeInfo(contentType);

            // Get MaPS competencies from maps_rubric
            const targetCompetencies = module.maps_rubric?.target_competencies || module.target_competencies || [];
            const mapsFramework = module.maps_framework_alignment || {};

            card.innerHTML = `
                <div class="module-card-header">
                    <div class="module-type-badge ${contentTypeInfo.class}">
                        <i class="fas ${contentTypeInfo.icon}" aria-hidden="true"></i>
                        <span>${contentTypeInfo.label}</span>
                    </div>
                    <span class="module-difficulty ${difficultyClass}">
                        ${module.difficulty_level}
                    </span>
                </div>
                <h3 class="module-card-title">${this.escapeHtml(module.title)}</h3>
                <p class="module-card-objective">${this.escapeHtml(module.learning_objective)}</p>
                
                <!-- MaPS Framework Alignment -->
                <div class="maps-alignment-badge">
                    <i class="fas fa-certificate" aria-hidden="true"></i>
                    <span>MaPS Aligned</span>
                </div>
                
                <div class="module-card-meta">
                    <span class="meta-item" title="Estimated time">
                        <i class="fas fa-clock" aria-hidden="true"></i>
                        ${module.estimated_minutes} min
                    </span>
                    <span class="meta-item" title="Focus Area">
                        <i class="fas ${focusAreaIcon}" aria-hidden="true"></i>
                        ${this.formatFocusArea(module.mi_focus_area)}
                    </span>
                </div>
                
                <!-- MaPS Competencies -->
                <div class="maps-competencies-list">
                    <span class="competencies-label">
                        <i class="fas fa-award" aria-hidden="true"></i>
                        MaPS Competencies:
                    </span>
                    <div class="competency-tags">
                        ${targetCompetencies.map(comp =>
                `<span class="competency-tag">${comp}</span>`
            ).join('')}
                    </div>
                </div>
                
                <!-- Tier Relevance -->
                ${mapsFramework.tier_relevance ? `
                    <div class="maps-tier-badge">
                        <i class="fas fa-layer-group" aria-hidden="true"></i>
                        ${mapsFramework.tier_relevance}
                    </div>
                ` : ''}
                
                ${this.createProgressIndicator(module)}
                <div class="module-card-actions">
                    <button class="btn-teal-primary btn-start-module" data-module-id="${module.id}">
                        ${module.is_completed ?
                    '<i class="fas fa-redo" aria-hidden="true"></i> Practice Again' :
                    module.user_attempts > 0 ?
                        '<i class="fas fa-play" aria-hidden="true"></i> Continue' :
                        '<i class="fas fa-play" aria-hidden="true"></i> Start Module'
                }
                    </button>
                </div>
            `;

            // Add click handler
            const startBtn = card.querySelector('.btn-start-module');
            if (startBtn && options.onStart) {
                startBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    options.onStart(module);
                });
            }

            return card;
        },

        /**
         * Get content type information for display
         * @param {string} contentType - The content type (shared, customer_facing, colleague_facing)
         * @returns {Object} Content type info with icon, label, and class
         */
        getContentTypeInfo(contentType) {
            const types = {
                'shared': {
                    icon: 'fa-shapes',
                    label: 'Core Skills',
                    class: 'type-shared',
                    description: 'Core MI techniques applicable to all contexts'
                },
                'customer_facing': {
                    icon: 'fa-users',
                    label: 'Customer-Facing',
                    class: 'type-customer',
                    description: 'MAPS financial scenarios'
                },
                'colleague_facing': {
                    icon: 'fa-user-group',
                    label: 'Colleague-Facing',
                    class: 'type-colleague',
                    description: 'MAPS workplace scenarios'
                }
            };
            return types[contentType] || types['shared'];
        },

        /**
         * Format focus area for display
         * @param {string} focusArea - The focus area code
         * @returns {string} Formatted focus area
         */
        formatFocusArea(focusArea) {
            const areas = {
                'rapport_building': 'Rapport Building',
                'probing_questions': 'Probing Questions',
                'customer_understanding': 'Reflections',
                'working_with_resistance': 'Working with Reluctance',
                'colleague_support': 'Colleague Support'
            };
            return areas[focusArea] || focusArea || 'General';
        },

        /**
         * Get focus area icon
         * @param {string} focusArea - The focus area
         * @returns {string} FontAwesome icon class
         */
        getFocusAreaIcon(focusArea) {
            const icons = {
                'rapport_building': 'fa-handshake',
                'probing_questions': 'fa-question',
                'customer_understanding': 'fa-ear-listen',
                'working_with_resistance': 'fa-shield-alt',
                'colleague_support': 'fa-users-cog'
            };
            return icons[focusArea] || 'fa-comment-alt';
        },

        /**
         * Create a learning path card
         * @param {Object} path - Learning path data
         * @param {Object} options - Optional configuration
         * @returns {HTMLElement} Path card element
         */
        createPathCard(path, options = {}) {
            const card = document.createElement('div');
            card.className = 'path-card';
            card.setAttribute('role', 'listitem');
            card.setAttribute('data-path-id', path.id);

            const progressPercent = path.progress_percent || 0;
            const isEnrolled = path.is_enrolled;

            // Get MaPS framework info from path structure
            const mapsTier = path.path_structure?.maps_tier || 'All Tiers';
            const mapsCompetencies = path.maps_competencies_covered || [];

            card.innerHTML = `
                <div class="path-card-header">
                    <i class="fas fa-route path-icon" aria-hidden="true"></i>
                    <h3 class="path-title">${this.escapeHtml(path.title)}</h3>
                </div>
                <p class="path-description">${this.escapeHtml(path.description || '')}</p>
                
                <!-- MaPS Alignment -->
                <div class="maps-path-badge">
                    <i class="fas fa-certificate" aria-hidden="true"></i>
                    <span>MaPS ${mapsTier}</span>
                </div>
                
                <div class="path-meta">
                    <span class="meta-item">
                        <i class="fas fa-cubes" aria-hidden="true"></i>
                        ${path.module_count} modules
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-clock" aria-hidden="true"></i>
                        ${path.estimated_total_minutes || '-'} min
                    </span>
                    ${path.target_audience ? `
                        <span class="meta-item">
                            <i class="fas fa-users" aria-hidden="true"></i>
                            ${path.target_audience}
                        </span>
                    ` : ''}
                </div>
                
                <!-- MaPS Competencies -->
                <div class="maps-competencies-list path-competencies">
                    <span class="competencies-label">
                        <i class="fas fa-award" aria-hidden="true"></i>
                        Competencies:
                    </span>
                    <div class="competency-tags">
                        ${mapsCompetencies.slice(0, 4).map(comp =>
                `<span class="competency-tag small">${comp}</span>`
            ).join('')}
                        ${mapsCompetencies.length > 4 ?
                    `<span class="competency-tag small">+${mapsCompetencies.length - 4} more</span>`
                    : ''}
                    </div>
                </div>
                
                ${isEnrolled ? `
                    <div class="path-progress">
                        <div class="progress-bar" role="progressbar" aria-valuenow="${progressPercent}" aria-valuemin="0" aria-valuemax="100">
                            <div class="progress-fill" style="width: ${progressPercent}%"></div>
                        </div>
                        <span class="progress-text">${Math.round(progressPercent)}% complete</span>
                    </div>
                ` : ''}
                <div class="path-actions">
                    <button class="btn-teal-primary ${isEnrolled ? 'btn-continue-path' : 'btn-enroll-path'}" data-path-id="${path.id}">
                        ${isEnrolled ?
                    '<i class="fas fa-play" aria-hidden="true"></i> Continue Path' :
                    '<i class="fas fa-sign-in-alt" aria-hidden="true"></i> Enroll'
                }
                    </button>
                </div>
            `;

            // Add click handler
            const actionBtn = card.querySelector('.btn-teal-primary');
            if (actionBtn && options.onAction) {
                actionBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    options.onAction(path);
                });
            }

            return card;
        },

        /**
         * Create a choice card for dialogue
         * @param {Object} choice - Choice point data
         * @param {string} letter - Choice letter (A, B, C)
         * @param {Function} onSelect - Selection callback
         * @returns {HTMLElement} Choice card element
         */
        createChoiceCard(choice, letter, onSelect) {
            const card = document.createElement('button');
            card.className = 'choice-card';
            card.setAttribute('role', 'radio');
            card.setAttribute('aria-checked', 'false');
            card.setAttribute('data-choice-id', choice.id);

            // Show MaPS competencies and principles if available
            const mapsInfo = choice.maps_principles ? `
                <div class="choice-maps-info">
                    <span class="maps-label"><i class="fas fa-certificate" aria-hidden="true"></i> MaPS:</span>
                    ${choice.maps_principles.map(p =>
                `<span class="maps-principle">${p}</span>`
            ).join(', ')}
                </div>
            ` : '';

            card.innerHTML = `
                <span class="choice-letter">${letter}</span>
                <div class="choice-content">
                    <p class="choice-text">${this.escapeHtml(choice.option_text || choice.response)}</p>
                    ${mapsInfo}
                    ${choice.preview_hint ? `
                        <span class="choice-hint">
                            <i class="fas fa-info-circle" aria-hidden="true"></i>
                            ${this.escapeHtml(choice.preview_hint)}
                        </span>
                    ` : ''}
                </div>
            `;

            card.addEventListener('click', () => {
                if (onSelect) onSelect(choice, letter);
            });

            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (onSelect) onSelect(choice, letter);
                }
            });

            return card;
        },

        /**
         * Create a timeline item for session review
         * @param {Object} turn - Turn data
         * @param {number} index - Turn index
         * @param {Function} onClick - Click callback
         * @returns {HTMLElement} Timeline item element
         */
        createTimelineItem(turn, index, onClick) {
            const item = document.createElement('div');
            item.className = 'timeline-item';
            item.setAttribute('role', 'listitem');

            const impactClass = this.getImpactClass(turn.rapport_impact, turn.resistance_impact);
            const mapsCompetencies = turn.maps_competencies || [];

            item.innerHTML = `
                <div class="timeline-turn-number">${index + 1}</div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="turn-choice">${turn.choice_letter}</span>
                        <span class="turn-impact ${impactClass}">
                            <i class="fas ${impactClass === 'positive' ? 'fa-arrow-up' : impactClass === 'negative' ? 'fa-arrow-down' : 'fa-minus'}" aria-hidden="true"></i>
                            ${turn.rapport_impact > 0 ? '+' : ''}${turn.rapport_impact}
                        </span>
                    </div>
                    <p class="turn-text">${this.escapeHtml(turn.response || turn.option_text)}</p>
                    <p class="turn-feedback">${this.escapeHtml(turn.feedback || '')}</p>
                    ${mapsCompetencies.length > 0 ? `
                        <div class="turn-competencies">
                            ${mapsCompetencies.map(c =>
                `<span class="competency-tag small">${c}</span>`
            ).join('')}
                        </div>
                    ` : ''}
                </div>
            `;

            if (onClick) {
                item.addEventListener('click', () => onClick(turn, index));
            }

            return item;
        },

        /**
         * Create progress indicator
         * @param {Object} module - Module data
         * @returns {string} HTML string for progress indicator
         */
        createProgressIndicator(module) {
            if (module.is_completed && module.competency_score) {
                return `
                    <div class="module-progress completed">
                        <div class="progress-score">
                            <i class="fas fa-check-circle" aria-hidden="true"></i>
                            <span>Completed: ${Math.round(module.competency_score * 100)}%</span>
                        </div>
                    </div>
                `;
            } else if (module.user_attempts > 0) {
                return `
                    <div class="module-progress in-progress">
                        <div class="progress-score">
                            <i class="fas fa-play-circle" aria-hidden="true"></i>
                            <span>In Progress (${module.user_attempts} attempt${module.user_attempts > 1 ? 's' : ''})</span>
                        </div>
                    </div>
                `;
            }
            return '';
        },

        /**
         * Get impact class based on scores
         * @param {number} rapportImpact - Rapport impact score
         * @param {number} resistanceImpact - Resistance impact score
         * @returns {string} CSS class
         */
        getImpactClass(rapportImpact, resistanceImpact) {
            if (rapportImpact > 0) return 'positive';
            if (rapportImpact < 0) return 'negative';
            return 'neutral';
        },

        /**
         * Show loading state
         * @param {HTMLElement} container - Container element
         * @param {string} message - Loading message
         */
        showLoading(container, message = 'Loading...') {
            container.innerHTML = `
                <div class="loading-state" role="status" aria-live="polite">
                    <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
                    <span>${this.escapeHtml(message)}</span>
                </div>
            `;
        },

        /**
         * Show empty state
         * @param {HTMLElement} container - Container element
         * @param {string} message - Empty message
         * @param {string} icon - FontAwesome icon class
         */
        showEmpty(container, message, icon = 'fa-search') {
            container.innerHTML = `
                <div class="empty-state" role="status" aria-live="polite">
                    <i class="fas ${icon}" aria-hidden="true"></i>
                    <p>${this.escapeHtml(message)}</p>
                </div>
            `;
        },

        /**
         * Show error state
         * @param {HTMLElement} container - Container element
         * @param {string} message - Error message
         * @param {Function} retryFn - Retry callback
         */
        showError(container, message, retryFn) {
            container.innerHTML = `
                <div class="error-state" role="alert">
                    <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
                    <p>${this.escapeHtml(message)}</p>
                    <button class="btn-text-link retry-btn">
                        <i class="fas fa-sync" aria-hidden="true"></i>
                        Try Again
                    </button>
                </div>
            `;
            const retryBtn = container.querySelector('.retry-btn');
            if (retryBtn && retryFn) {
                retryBtn.addEventListener('click', retryFn);
            }
        },

        /**
         * Escape HTML to prevent XSS
         * @param {string} text - Text to escape
         * @returns {string} Escaped text
         */
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Export to window
    window.MIComponents = MIComponents;

})();
