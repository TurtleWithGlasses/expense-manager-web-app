/**
 * Achievement Notification System - Phase 3
 *
 * Displays toast notifications when users unlock new achievements
 * Polls the achievements API and shows animated notifications
 */

class AchievementNotificationSystem {
    constructor() {
        this.pollInterval = 30000; // Poll every 30 seconds
        this.lastCheckTime = null;
        this.notificationQueue = [];
        this.isProcessingQueue = false;
        this.initialized = false;
    }

    /**
     * Initialize the notification system
     */
    init() {
        if (this.initialized) return;

        // Create toast container if it doesn't exist
        this.createToastContainer();

        // Start polling for new achievements
        this.startPolling();

        this.initialized = true;
        console.log('Achievement notification system initialized');
    }

    /**
     * Create the toast container element
     */
    createToastContainer() {
        if (document.getElementById('achievement-toast-container')) return;

        const container = document.createElement('div');
        container.id = 'achievement-toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    /**
     * Start polling for new achievements
     */
    startPolling() {
        // Initial check after 5 seconds
        setTimeout(() => this.checkForNewAchievements(), 5000);

        // Then poll at regular intervals
        setInterval(() => this.checkForNewAchievements(), this.pollInterval);
    }

    /**
     * Check for new achievements from the API
     */
    async checkForNewAchievements() {
        try {
            const response = await fetch('/api/achievements/recent?limit=5');
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success || !data.achievements) return;

            // Filter for newly unlocked achievements (is_new flag)
            const newAchievements = data.achievements.filter(achievement =>
                achievement.is_new === true
            );

            if (newAchievements.length > 0) {
                // Add to notification queue
                newAchievements.forEach(userAchievement => {
                    // Flatten the nested structure for easier access
                    const flattenedAchievement = {
                        id: userAchievement.id,
                        name: userAchievement.achievement.name,
                        description: userAchievement.achievement.description,
                        tier: userAchievement.achievement.tier,
                        icon: userAchievement.achievement.icon_name,
                        points: userAchievement.achievement.points,
                        category: userAchievement.achievement.category,
                        badge_id: null, // Would need to check badge relationship
                        is_new: userAchievement.is_new,
                        earned_at: userAchievement.earned_at
                    };
                    this.queueNotification(flattenedAchievement);
                });

                // Process the queue
                this.processNotificationQueue();
            }

        } catch (error) {
            console.error('Error checking for new achievements:', error);
        }
    }

    /**
     * Add achievement to notification queue
     */
    queueNotification(achievement) {
        if (!this.notificationQueue.find(a => a.id === achievement.id)) {
            this.notificationQueue.push(achievement);
        }
    }

    /**
     * Process notification queue (show one at a time with delay)
     */
    async processNotificationQueue() {
        if (this.isProcessingQueue || this.notificationQueue.length === 0) return;

        this.isProcessingQueue = true;

        while (this.notificationQueue.length > 0) {
            const achievement = this.notificationQueue.shift();
            await this.showAchievementNotification(achievement);

            // Wait 4 seconds before showing next notification
            await this.sleep(4000);
        }

        // Mark all as viewed after showing
        await this.markAchievementsAsViewed();

        this.isProcessingQueue = false;
    }

    /**
     * Show achievement notification toast
     */
    async showAchievementNotification(achievement) {
        return new Promise((resolve) => {
            const container = document.getElementById('achievement-toast-container');
            if (!container) {
                resolve();
                return;
            }

            // Create toast element
            const toastId = `achievement-toast-${achievement.id}`;
            const toastEl = this.createToastElement(toastId, achievement);
            container.appendChild(toastEl);

            // Initialize Bootstrap toast
            const bsToast = new bootstrap.Toast(toastEl, {
                autohide: true,
                delay: 5000
            });

            // Play sound effect if available
            this.playUnlockSound();

            // Show the toast
            bsToast.show();

            // Remove from DOM after hidden
            toastEl.addEventListener('hidden.bs.toast', () => {
                toastEl.remove();
                resolve();
            });

            // Auto-resolve if toast doesn't hide
            setTimeout(() => resolve(), 6000);
        });
    }

    /**
     * Create toast HTML element
     */
    createToastElement(toastId, achievement) {
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = 'toast achievement-toast';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        // Get tier color
        const tierColor = this.getTierColor(achievement.tier);
        const tierIcon = this.getTierIcon(achievement.tier);

        toast.innerHTML = `
            <div class="toast-header" style="background: linear-gradient(135deg, ${tierColor}22 0%, ${tierColor}11 100%); border-bottom: 2px solid ${tierColor};">
                <i class="bi ${tierIcon} me-2" style="color: ${tierColor}; font-size: 1.2rem;"></i>
                <strong class="me-auto">Achievement Unlocked!</strong>
                <small class="text-muted">${achievement.tier}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                <div class="d-flex align-items-center">
                    <div class="achievement-icon me-3" style="font-size: 2.5rem;">
                        ${achievement.icon || '🏆'}
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1 fw-bold">${achievement.name}</h6>
                        <p class="mb-2 small text-muted">${achievement.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge" style="background-color: ${tierColor};">
                                +${achievement.points} XP
                            </span>
                            ${achievement.badge_id ? '<span class="badge bg-secondary"><i class="bi bi-award"></i> Badge Earned</span>' : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;

        return toast;
    }

    /**
     * Get color for achievement tier
     */
    getTierColor(tier) {
        const colors = {
            'bronze': '#CD7F32',
            'silver': '#C0C0C0',
            'gold': '#FFD700',
            'platinum': '#E5E4E2'
        };
        return colors[tier.toLowerCase()] || '#6c757d';
    }

    /**
     * Get icon for achievement tier
     */
    getTierIcon(tier) {
        const icons = {
            'bronze': 'bi-award-fill',
            'silver': 'bi-star-fill',
            'gold': 'bi-trophy-fill',
            'platinum': 'bi-gem'
        };
        return icons[tier.toLowerCase()] || 'bi-award';
    }

    /**
     * Play unlock sound effect
     */
    playUnlockSound() {
        try {
            // Only play if user has interacted with page (browser autoplay policy)
            const audio = new Audio('/static/sounds/achievement-unlock.mp3');
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Silently fail if sound can't play
            });
        } catch (error) {
            // Sound file might not exist, that's okay
        }
    }

    /**
     * Mark achievements as viewed via API
     */
    async markAchievementsAsViewed() {
        try {
            await fetch('/api/achievements/mark-viewed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Error marking achievements as viewed:', error);
        }
    }

    /**
     * Manually trigger achievement check (call after user actions)
     */
    async triggerCheck() {
        try {
            const response = await fetch('/api/achievements/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) return;

            const data = await response.json();

            if (data.newly_unlocked && data.newly_unlocked.length > 0) {
                // Add newly unlocked achievements to queue
                data.newly_unlocked.forEach(userAchievement => {
                    // Flatten the nested structure
                    const flattenedAchievement = {
                        id: userAchievement.id,
                        name: userAchievement.achievement.name,
                        description: userAchievement.achievement.description,
                        tier: userAchievement.achievement.tier,
                        icon: userAchievement.achievement.icon_name,
                        points: userAchievement.achievement.points,
                        category: userAchievement.achievement.category,
                        badge_id: null,
                        is_new: userAchievement.is_new,
                        earned_at: userAchievement.earned_at
                    };
                    this.queueNotification(flattenedAchievement);
                });

                // Process the queue
                this.processNotificationQueue();
            }

        } catch (error) {
            console.error('Error triggering achievement check:', error);
        }
    }

    /**
     * Helper: Sleep/delay function
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize global instance
const achievementNotifications = new AchievementNotificationSystem();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        achievementNotifications.init();
    });
} else {
    achievementNotifications.init();
}

// Export for manual triggers from other scripts
window.achievementNotifications = achievementNotifications;
