/**
 * PWA Installation and Service Worker Registration
 * Handles "Add to Home Screen" functionality and service worker lifecycle
 */

(function() {
  'use strict';

  let deferredPrompt = null;
  let isServiceWorkerSupported = 'serviceWorker' in navigator;
  let isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

  /**
   * Register Service Worker
   */
  async function registerServiceWorker() {
    if (!isServiceWorkerSupported) {
      console.log('[PWA] Service Workers not supported');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.register('/static/service-worker.js', {
        scope: '/'
      });

      console.log('[PWA] Service Worker registered:', registration.scope);

      // Check for updates periodically
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('[PWA] New Service Worker found');

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New service worker available
            showUpdateNotification();
          }
        });
      });

      // Check for updates every hour
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000);

    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  }

  /**
   * Show update notification when new version available
   */
  function showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'pwa-update-notification';
    notification.innerHTML = `
      <div class="pwa-update-content">
        <div class="pwa-update-icon">🔄</div>
        <div class="pwa-update-text">
          <strong>Update Available</strong>
          <p>A new version of BudgetPulse is ready!</p>
        </div>
        <button class="pwa-update-btn" onclick="window.location.reload()">Update Now</button>
      </div>
    `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .pwa-update-notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--card-bg, #252b3d);
        border: 1px solid var(--border-color, #2a3550);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        max-width: 350px;
        animation: slideIn 0.3s ease-out;
      }

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

      .pwa-update-content {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .pwa-update-icon {
        font-size: 32px;
      }

      .pwa-update-text {
        flex: 1;
      }

      .pwa-update-text strong {
        display: block;
        color: var(--text-primary, #e5e7eb);
        margin-bottom: 4px;
      }

      .pwa-update-text p {
        margin: 0;
        color: var(--text-secondary, #9ca3af);
        font-size: 14px;
      }

      .pwa-update-btn {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        white-space: nowrap;
      }

      .pwa-update-btn:hover {
        background: #2563eb;
      }

      @media (max-width: 640px) {
        .pwa-update-notification {
          left: 20px;
          right: 20px;
          bottom: 20px;
          max-width: none;
        }
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(notification);

    // Auto-remove after 10 seconds
    setTimeout(() => {
      notification.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => notification.remove(), 300);
    }, 10000);
  }

  /**
   * Handle beforeinstallprompt event
   */
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] Install prompt available');

    // Prevent default mini-infobar
    e.preventDefault();

    // Store the event for later use
    deferredPrompt = e;

    // Show custom install button
    showInstallButton();
  });

  /**
   * Show custom install button
   */
  function showInstallButton() {
    // Check if already installed
    if (isStandalone) {
      console.log('[PWA] Already installed');
      return;
    }

    // Create install banner
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.className = 'pwa-install-banner';
    banner.innerHTML = `
      <div class="pwa-install-content">
        <div class="pwa-install-icon">
          <img src="/static/money_icon.png" alt="BudgetPulse" width="48" height="48">
        </div>
        <div class="pwa-install-text">
          <strong>Install BudgetPulse</strong>
          <p>Install app for quick access and offline use</p>
        </div>
        <button class="pwa-install-btn" id="pwa-install-btn">Install</button>
        <button class="pwa-install-close" id="pwa-install-close" aria-label="Close">×</button>
      </div>
    `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .pwa-install-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--card-bg, #252b3d);
        border-top: 1px solid var(--border-color, #2a3550);
        padding: 16px;
        z-index: 9999;
        animation: slideUp 0.3s ease-out;
        box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.2);
      }

      @keyframes slideUp {
        from {
          transform: translateY(100%);
        }
        to {
          transform: translateY(0);
        }
      }

      .pwa-install-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 16px;
      }

      .pwa-install-icon img {
        border-radius: 12px;
        display: block;
      }

      .pwa-install-text {
        flex: 1;
      }

      .pwa-install-text strong {
        display: block;
        color: var(--text-primary, #e5e7eb);
        margin-bottom: 4px;
        font-size: 16px;
      }

      .pwa-install-text p {
        margin: 0;
        color: var(--text-secondary, #9ca3af);
        font-size: 14px;
      }

      .pwa-install-btn {
        background: #3b82f6;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 15px;
        font-weight: 500;
        white-space: nowrap;
      }

      .pwa-install-btn:hover {
        background: #2563eb;
      }

      .pwa-install-close {
        background: transparent;
        border: none;
        color: var(--text-secondary, #9ca3af);
        font-size: 32px;
        line-height: 1;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .pwa-install-close:hover {
        color: var(--text-primary, #e5e7eb);
      }

      @media (max-width: 640px) {
        .pwa-install-content {
          flex-wrap: wrap;
        }

        .pwa-install-btn {
          width: 100%;
          margin-top: 8px;
        }

        .pwa-install-close {
          position: absolute;
          top: 16px;
          right: 16px;
        }
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(banner);

    // Add event listeners
    document.getElementById('pwa-install-btn').addEventListener('click', installPWA);
    document.getElementById('pwa-install-close').addEventListener('click', () => {
      banner.style.animation = 'slideUp 0.3s ease-out reverse';
      setTimeout(() => banner.remove(), 300);

      // Remember user dismissed
      localStorage.setItem('pwa-install-dismissed', Date.now());
    });

    // Auto-hide if user dismissed recently (within 7 days)
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed && Date.now() - dismissed < 7 * 24 * 60 * 60 * 1000) {
      banner.remove();
    }
  }

  /**
   * Install PWA
   */
  async function installPWA() {
    if (!deferredPrompt) {
      console.log('[PWA] No install prompt available');
      return;
    }

    // Show install prompt
    deferredPrompt.prompt();

    // Wait for user choice
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[PWA] User choice:', outcome);

    if (outcome === 'accepted') {
      console.log('[PWA] App installed');
      // Remove install banner
      const banner = document.getElementById('pwa-install-banner');
      if (banner) {
        banner.remove();
      }
    }

    // Clear deferred prompt
    deferredPrompt = null;
  }

  /**
   * Track app install
   */
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');

    // Remove install banner
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.remove();
    }

    // Show thank you message
    showToast('✅ BudgetPulse installed! You can now use it offline.', 'success');
  });

  /**
   * Show toast notification
   */
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `pwa-toast pwa-toast-${type}`;
    toast.textContent = message;

    const style = document.createElement('style');
    style.textContent = `
      .pwa-toast {
        position: fixed;
        top: 80px;
        right: 20px;
        background: var(--card-bg, #252b3d);
        color: var(--text-primary, #e5e7eb);
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10001;
        animation: slideIn 0.3s ease-out;
        max-width: 350px;
      }

      .pwa-toast-success {
        border-left: 4px solid #10b981;
      }

      .pwa-toast-info {
        border-left: 4px solid #3b82f6;
      }

      @media (max-width: 640px) {
        .pwa-toast {
          left: 20px;
          right: 20px;
        }
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  /**
   * Check online/offline status
   */
  function updateOnlineStatus() {
    if (!navigator.onLine) {
      showToast('📡 You are offline. Some features may be limited.', 'info');
    }
  }

  window.addEventListener('online', () => {
    showToast('✅ Back online!', 'success');
  });

  window.addEventListener('offline', () => {
    showToast('📡 You are offline', 'info');
  });

  /**
   * Initialize PWA features
   */
  function initPWA() {
    console.log('[PWA] Initializing...');

    // Register service worker
    registerServiceWorker();

    // Check online status
    updateOnlineStatus();

    // Log standalone mode
    if (isStandalone) {
      console.log('[PWA] Running in standalone mode');
    }

    console.log('[PWA] Initialization complete');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPWA);
  } else {
    initPWA();
  }

})();
