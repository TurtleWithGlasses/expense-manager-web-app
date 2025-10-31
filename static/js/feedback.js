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

    // Build modal HTML
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <div class="modal-icon ${iconClass}">
            ${icons[danger ? 'danger' : type] || icons.info}
          </div>
          <h3 class="modal-title">${title}</h3>
        </div>
        <div class="modal-body">
          ${message}
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" data-action="cancel">${cancelText}</button>
          <button class="btn ${confirmClass}" data-action="confirm">${confirmText}</button>
        </div>
      </div>
    `;

    // Add to body
    document.body.appendChild(overlay);

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
