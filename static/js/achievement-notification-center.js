/**
 * Achievement Notification Center - Phase 3
 *
 * Bell-based notification system for achievements
 * Shows a notification bell icon with badge count
 * Displays dropdown panel with list of achievements when clicked
 */

class AchievementNotificationCenter {
    constructor() {
        this.bell = null;
        this.badge = null;
        this.dropdown = null;
        this.achievementList = null;
        this.pollInterval = 30000; // Poll every 30 seconds
        this.isDropdownOpen = false;
    }

    /**
     * Initialize the notification center
     */
    init() {
        // Get DOM elements
        this.bell = document.getElementById('achievement-bell');
        this.badge = document.getElementById('achievement-badge');
        this.dropdown = document.getElementById('achievement-dropdown');
        this.achievementList = document.getElementById('achievement-list');

        if (!this.bell || !this.badge || !this.dropdown) {
            console.warn('Achievement notification center elements not found');
            return;
        }

        // Setup event listeners
        this.setupEventListeners();

        // Initial load
        this.loadNotifications();

        // Start polling
        setInterval(() => this.loadNotifications(), this.pollInterval);

        console.log('Achievement notification center initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Toggle dropdown on bell click
        this.bell.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Mark all as viewed
        const markAllBtn = document.getElementById('mark-all-viewed');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllAsViewed());
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isDropdownOpen &&
                !this.dropdown.contains(e.target) &&
                !this.bell.contains(e.target)) {
                this.closeDropdown();
            }
        });
    }

    /**
     * Load notifications from API
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/achievements/recent?limit=10');
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success || !data.achievements) return;

            // Filter for new achievements
            const newAchievements = data.achievements.filter(ua => ua.is_new === true);

            // Update badge
            this.updateBadge(newAchievements.length);

            // Update dropdown list
            this.updateDropdownList(data.achievements);

        } catch (error) {
            console.error('Error loading achievement notifications:', error);
        }
    }

    /**
     * Update notification badge
     */
    updateBadge(count) {
        if (count > 0) {
            this.badge.textContent = count > 9 ? '9+' : count;
            this.badge.style.display = 'block';
            this.bell.classList.add('has-notifications');
        } else {
            this.badge.style.display = 'none';
            this.bell.classList.remove('has-notifications');
        }
    }

    /**
     * Update dropdown achievement list
     */
    updateDropdownList(achievements) {
        if (!achievements || achievements.length === 0) {
            this.achievementList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-bell-slash" style="font-size: 2rem;"></i>
                    <p class="mb-0 mt-2">No achievements yet</p>
                </div>
            `;
            return;
        }

        // Create achievement items
        const items = achievements.map(ua => this.createAchievementItem(ua)).join('');
        this.achievementList.innerHTML = items;
    }

    /**
     * Convert icon name to emoji
     */
    getIconEmoji(iconName) {
        const iconMap = {
            'trophy': '🏆',
            'fire': '🔥',
            'star': '⭐',
            'piggy-bank': '🐷',
            'dollar': '💵',
            'ban': '🚫',
            'scissors': '✂️',
            'crown': '👑',
            'bird': '🐦',
            'sunrise': '🌅',
            'calendar-weekend': '📅',
            'graph-up': '📈',
            'shield-check': '🛡️',
            'graph-up-arrow': '📊',
            'check-circle': '✅',
            'award': '🏅',
            'x-circle': '❌',
            'wallet': '👛',
            'house': '🏠',
            'flag': '🚩',
            'clock': '⏰',
            'graph': '📉',
            'diagram': '📋',
            'download': '⬇️'
        };
        return iconMap[iconName] || '🏆'; // Default to trophy
    }

    /**
     * Create achievement item HTML
     */
    createAchievementItem(userAchievement) {
        const ach = userAchievement.achievement || {};
        const icon = this.getIconEmoji(ach.icon_name);
        const name = ach.name || 'Achievement';
        const description = ach.description || 'Unlocked';
        const points = ach.points || 0;
        const tier = ach.tier || 'bronze';
        const isNew = userAchievement.is_new;
        const earnedAt = userAchievement.earned_at ? this.timeAgo(userAchievement.earned_at) : 'Just now';

        const tierColor = this.getTierColor(tier);
        const tierEmoji = this.getTierEmoji(tier);

        return `
            <div class="achievement-item ${isNew ? 'unread' : ''}" data-achievement-id="${userAchievement.id}">
                <div class="achievement-item-icon">${icon}</div>
                <div class="achievement-item-content">
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <div class="achievement-item-title">${name}</div>
                        <span class="tier-mini-badge" style="background-color: ${tierColor};" title="${tier}">
                            ${tierEmoji}
                        </span>
                    </div>
                    <div class="achievement-item-description">${description}</div>
                    <div class="achievement-item-meta">
                        <span class="achievement-item-xp" style="background-color: ${tierColor};">
                            <i class="bi bi-star-fill" style="font-size: 0.7rem;"></i> +${points} XP
                        </span>
                        <span class="achievement-item-time">${earnedAt}</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Toggle dropdown visibility
     */
    toggleDropdown() {
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    /**
     * Open dropdown
     */
    openDropdown() {
        this.dropdown.style.display = 'block';
        this.isDropdownOpen = true;

        // Mark achievements as viewed after short delay
        setTimeout(() => this.markAllAsViewed(), 1000);
    }

    /**
     * Close dropdown
     */
    closeDropdown() {
        this.dropdown.style.display = 'none';
        this.isDropdownOpen = false;
    }

    /**
     * Mark all achievements as viewed
     */
    async markAllAsViewed() {
        try {
            const response = await fetch('/api/achievements/mark-viewed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Update badge
                this.updateBadge(0);

                // Remove unread class from all items
                const unreadItems = this.achievementList.querySelectorAll('.achievement-item.unread');
                unreadItems.forEach(item => item.classList.remove('unread'));
            }
        } catch (error) {
            console.error('Error marking achievements as viewed:', error);
        }
    }

    /**
     * Get tier color
     */
    getTierColor(tier) {
        const colors = {
            'bronze': '#CD7F32',
            'silver': '#9CA3AF',  // Darker silver for better visibility
            'gold': '#EAB308',     // Slightly darker gold
            'platinum': '#8B5CF6'  // Purple for platinum
        };
        return colors[tier?.toLowerCase()] || '#CD7F32';
    }

    /**
     * Get tier emoji
     */
    getTierEmoji(tier) {
        const emojis = {
            'bronze': '🥉',
            'silver': '🥈',
            'gold': '🥇',
            'platinum': '💎'
        };
        return emojis[tier?.toLowerCase()] || '🥉';
    }

    /**
     * Format time ago
     */
    timeAgo(timestamp) {
        const now = new Date();
        const past = new Date(timestamp);
        const seconds = Math.floor((now - past) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return `${Math.floor(seconds / 604800)}w ago`;
    }

    /**
     * Manually trigger check (call after user actions)
     */
    async triggerCheck() {
        try {
            const response = await fetch('/api/achievements/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Reload notifications to show new achievements
                await this.loadNotifications();
            }
        } catch (error) {
            console.error('Error triggering achievement check:', error);
        }
    }
}

// Initialize when DOM is ready
const achievementNotificationCenter = new AchievementNotificationCenter();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        achievementNotificationCenter.init();
    });
} else {
    achievementNotificationCenter.init();
}

// Export for use in other scripts
window.achievementNotificationCenter = achievementNotificationCenter;
