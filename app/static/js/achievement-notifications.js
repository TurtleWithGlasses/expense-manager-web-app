/**
 * Achievement Notification System - Phase 3: Full Gamification
 *
 * Displays toast notifications when achievements are unlocked,
 * level up occurs, or badges are earned.
 */

class AchievementNotificationService {
  constructor() {
    this.container = null;
    this.checkInterval = null;
    this.lastCheckTime = Date.now();
    this.init();
  }

  init() {
    // Create notification container
    this.container = document.createElement('div');
    this.container.id = 'achievement-notifications';
    this.container.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 10000;
      max-width: 400px;
    `;
    document.body.appendChild(this.container);

    // Auto-check for new achievements periodically (every 5 minutes)
    this.checkInterval = setInterval(() => this.checkForNewAchievements(), 300000);
  }

  /**
   * Show a notification for an unlocked achievement
   */
  showAchievementUnlock(achievement) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification fade-in';
    notification.style.cssText = `
      background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      margin-bottom: 1rem;
      box-shadow: 0 8px 24px rgba(34, 197, 94, 0.3);
      cursor: pointer;
      transition: all 0.3s ease;
      animation: slideIn 0.5s ease;
    `;

    notification.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="achievement-icon me-3" style="
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
        ">
          🏆
        </div>
        <div class="flex-grow-1">
          <div class="fw-bold mb-1">Achievement Unlocked!</div>
          <div style="font-size: 0.95rem; opacity: 0.95;">${achievement.name}</div>
          <div style="font-size: 0.85rem; opacity: 0.8;">+${achievement.points} points</div>
        </div>
        <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
      </div>
    `;

    // Click to view achievements page
    notification.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-close')) return;
      window.location.href = '/achievements';
    });

    this.container.appendChild(notification);

    // Auto-dismiss after 8 seconds
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 300);
    }, 8000);

    // Play sound effect (if enabled)
    this.playUnlockSound();
  }

  /**
   * Show a notification for level up
   */
  showLevelUp(newLevel, rankName) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification fade-in';
    notification.style.cssText = `
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      margin-bottom: 1rem;
      box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
      cursor: pointer;
      transition: all 0.3s ease;
      animation: slideIn 0.5s ease, pulse 0.5s ease;
    `;

    notification.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="achievement-icon me-3" style="
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
        ">
          ⬆️
        </div>
        <div class="flex-grow-1">
          <div class="fw-bold mb-1">Level Up!</div>
          <div style="font-size: 1.1rem; opacity: 0.95;">Level ${newLevel}</div>
          <div style="font-size: 0.85rem; opacity: 0.8;">${rankName}</div>
        </div>
        <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
      </div>
    `;

    notification.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-close')) return;
      window.location.href = '/achievements';
    });

    this.container.appendChild(notification);

    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 300);
    }, 10000);

    this.playLevelUpSound();
  }

  /**
   * Show a notification for a new badge
   */
  showBadgeEarned(badge) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification fade-in';
    notification.style.cssText = `
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      margin-bottom: 1rem;
      box-shadow: 0 8px 24px rgba(245, 158, 11, 0.3);
      cursor: pointer;
      transition: all 0.3s ease;
      animation: slideIn 0.5s ease;
    `;

    notification.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="achievement-icon me-3" style="
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
        ">
          🎖️
        </div>
        <div class="flex-grow-1">
          <div class="fw-bold mb-1">Badge Earned!</div>
          <div style="font-size: 0.95rem; opacity: 0.95;">${badge.name}</div>
        </div>
        <button class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
      </div>
    `;

    notification.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-close')) return;
      window.location.href = '/achievements';
    });

    this.container.appendChild(notification);

    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 300);
    }, 8000);

    this.playUnlockSound();
  }

  /**
   * Check for new achievements and notify
   */
  async checkForNewAchievements() {
    try {
      const response = await fetch('/api/achievements/');
      const data = await response.json();

      // Filter for new achievements (is_new = true)
      const newAchievements = data.achievements.filter(a => a.is_new && a.is_unlocked);

      newAchievements.forEach(achievement => {
        this.showAchievementUnlock(achievement);
      });

      // Mark as viewed if any new ones were found
      if (newAchievements.length > 0) {
        await fetch('/api/achievements/mark-viewed', { method: 'POST' });
      }
    } catch (error) {
      console.error('Error checking for new achievements:', error);
    }
  }

  /**
   * Manually trigger achievement check (call after user actions)
   */
  async triggerCheck() {
    try {
      const response = await fetch('/api/achievements/check', { method: 'POST' });
      const data = await response.json();

      if (data.newly_unlocked && data.newly_unlocked.length > 0) {
        data.newly_unlocked.forEach(achievement => {
          this.showAchievementUnlock(achievement);
        });
      }
    } catch (error) {
      console.error('Error triggering achievement check:', error);
    }
  }

  /**
   * Play unlock sound effect
   */
  playUnlockSound() {
    // Check if user has sound enabled (you can add a setting for this)
    const soundEnabled = localStorage.getItem('achievementSoundsEnabled') !== 'false';
    if (!soundEnabled) return;

    // Create a simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      // Silently fail if audio not supported
    }
  }

  /**
   * Play level up sound effect
   */
  playLevelUpSound() {
    const soundEnabled = localStorage.getItem('achievementSoundsEnabled') !== 'false';
    if (!soundEnabled) return;

    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Play a sequence of notes
      oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C
      oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E
      oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      // Silently fail if audio not supported
    }
  }

  /**
   * Clean up on destroy
   */
  destroy() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
    if (this.container) {
      this.container.remove();
    }
  }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
  }

  .achievement-notification:hover {
    transform: translateX(-5px) scale(1.02);
  }
`;
document.head.appendChild(style);

// Initialize the service globally
window.achievementNotifications = new AchievementNotificationService();

// Helper function to check achievements after actions
window.checkAchievements = async function() {
  await window.achievementNotifications.triggerCheck();
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AchievementNotificationService;
}
