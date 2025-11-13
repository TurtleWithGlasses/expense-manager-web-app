/**
 * Feedback System - Toast Notifications & Confirmation Modals
 * Phase 6: Loading States & Feedback
 */

// ============================================
// TOAST NOTIFICATIONS
// ============================================

const Toast = {
  container: null,

  // Initialize toast container
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  // Show toast notification
  show(options = {}) {
    this.init();

    const {
      type = 'info',
      title = '',
      message = '',
      duration = 5000,
      closable = true
    } = options;

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Icon mapping
    const icons = {
      success: '<i class="bi bi-check-circle-fill"></i>',
      error: '<i class="bi bi-x-circle-fill"></i>',
      warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
      info: '<i class="bi bi-info-circle-fill"></i>'
    };

    // Build toast HTML
    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || icons.info}</div>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        ${message ? `<div class="toast-message">${message}</div>` : ''}
      </div>
      ${closable ? '<button class="toast-close" aria-label="Close"><i class="bi bi-x"></i></button>' : ''}
    `;

    // Add to container
    this.container.appendChild(toast);

    // Close button handler
    if (closable) {
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', () => this.remove(toast));
    }

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => this.remove(toast), duration);
    }

    return toast;
  },

  // Remove toast with animation
  remove(toast) {
    toast.classList.add('toast-exit');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  },

  // Shorthand methods
  success(message, title = 'Success') {
    return this.show({ type: 'success', title, message });
  },

  error(message, title = 'Error') {
    return this.show({ type: 'error', title, message });
  },

  warning(message, title = 'Warning') {
    return this.show({ type: 'warning', title, message });
  },

  info(message, title = 'Info') {
    return this.show({ type: 'info', title, message });
  }
};

// ============================================
// CONFIRMATION MODALS
// ============================================

const ConfirmModal = {
  // Show confirmation modal
  show(options = {}) {
    const {
      type = 'warning',
      title = 'Confirm Action',
      message = 'Are you sure you want to proceed?',
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      onConfirm = () => {},
      onCancel = () => {},
      danger = false
    } = options;

    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    // Icon mapping
    const icons = {
      warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
      danger: '<i class="bi bi-trash-fill"></i>',
      info: '<i class="bi bi-info-circle-fill"></i>'
    };

    const iconClass = danger ? 'modal-icon-danger' : `modal-icon-${type}`;
    const confirmClass = danger ? 'btn-danger' : 'btn-primary';

    // Build modal HTML with inline styles for guaranteed visibility
    overlay.innerHTML = `
      <div class="modal" style="position: relative !important; z-index: 10001 !important; background: #1e2740 !important; border: 2px solid rgba(255, 255, 255, 0.2) !important; border-radius: 12px !important; box-shadow: 0 25px 70px rgba(0, 0, 0, 0.8) !important; max-width: 500px !important; width: 90% !important; display: block !important; visibility: visible !important; opacity: 1 !important;">
        <div class="modal-header" style="display: flex !important; align-items: center !important; gap: 1rem !important; padding: 1.5rem !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;">
          <div class="modal-icon ${iconClass}" style="flex-shrink: 0 !important; width: 48px !important; height: 48px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1.5rem !important; border-radius: 50% !important; background: rgba(239, 68, 68, 0.15) !important; color: #ef4444 !important;">
            ${icons[danger ? 'danger' : type] || icons.info}
          </div>
          <h3 class="modal-title" style="flex: 1 !important; font-size: 1.25rem !important; font-weight: 700 !important; color: #e8ecf3 !important; margin: 0 !important;">${title}</h3>
        </div>
        <div class="modal-body" style="padding: 1.5rem !important; color: #9aa3b2 !important; font-size: 1rem !important; line-height: 1.6 !important;">
          ${message}
        </div>
        <div class="modal-footer" style="display: flex !important; gap: 0.75rem !important; padding: 1.5rem !important; border-top: 1px solid rgba(255, 255, 255, 0.1) !important; justify-content: flex-end !important;">
          <button class="btn btn-ghost" data-action="cancel" style="padding: 0.625rem 1.25rem !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 8px !important; background: transparent !important; color: #9aa3b2 !important; font-size: 0.95rem !important; cursor: pointer !important; transition: all 0.2s !important;">${cancelText}</button>
          <button class="btn ${confirmClass}" data-action="confirm" style="padding: 0.625rem 1.25rem !important; border: none !important; border-radius: 8px !important; background: #dc3545 !important; color: white !important; font-size: 0.95rem !important; font-weight: 600 !important; cursor: pointer !important; transition: all 0.2s !important;">${confirmText}</button>
        </div>
      </div>
    `;

    // Add to body
    document.body.appendChild(overlay);

    // Force reflow to ensure styles are applied
    overlay.offsetHeight;

    // Button handlers
    const confirmBtn = overlay.querySelector('[data-action="confirm"]');
    const cancelBtn = overlay.querySelector('[data-action="cancel"]');

    const close = (confirmed) => {
      overlay.classList.add('modal-exit');
      setTimeout(() => {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      }, 200);

      if (confirmed) {
        onConfirm();
      } else {
        onCancel();
      }
    };

    confirmBtn.addEventListener('click', () => close(true));
    cancelBtn.addEventListener('click', () => close(false));

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        close(false);
      }
    });

    // Close on Escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        close(false);
        document.removeEventListener('keydown', handleEscape);
      }
    };
    document.addEventListener('keydown', handleEscape);

    return {
      close: () => close(false)
    };
  },

  // Shorthand for delete confirmations
  confirmDelete(itemName, onConfirm) {
    return this.show({
      type: 'danger',
      danger: true,
      title: 'Delete Confirmation',
      message: `Are you sure you want to delete "${itemName}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      onConfirm
    });
  }
};

// ============================================
// LOADING STATES
// ============================================

const Loading = {
  // Add loading state to button
  button(button, loading = true) {
    if (loading) {
      button.classList.add('btn-loading');
      button.disabled = true;
      button.dataset.originalText = button.innerHTML;
    } else {
      button.classList.remove('btn-loading');
      button.disabled = false;
      if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
      }
    }
  },

  // Show spinner in element
  show(element, size = 'md') {
    const spinner = document.createElement('div');
    spinner.className = `spinner spinner-${size}`;
    spinner.style.margin = '20px auto';
    element.innerHTML = '';
    element.appendChild(spinner);
  }
};

// ============================================
// GLOBAL EXPORTS
// ============================================

// Make available globally
window.Toast = Toast;
window.ConfirmModal = ConfirmModal;
window.Loading = Loading;

// Helper function to replace alert()
window.showToast = Toast.show.bind(Toast);
window.confirmAction = ConfirmModal.show.bind(ConfirmModal);
