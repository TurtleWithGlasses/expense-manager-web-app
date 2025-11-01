/**
 * Advanced Features
 * Phase 11: Advanced filtering, bulk operations, search, and more
 */

// ==============================================
// ADVANCED FILTERING SYSTEM
// ==============================================

class AdvancedFilters {
  constructor() {
    this.filters = {
      dateRange: { start: null, end: null },
      categories: [],
      amountRange: { min: null, max: null },
      searchQuery: '',
      tags: [],
      sortBy: 'date',
      sortOrder: 'desc'
    };
    this.savedFilters = this.loadSavedFilters();
  }

  /**
   * Set date range filter
   */
  setDateRange(start, end) {
    this.filters.dateRange = { start, end };
    this.applyFilters();
  }

  /**
   * Set amount range filter
   */
  setAmountRange(min, max) {
    this.filters.amountRange = { min, max };
    this.applyFilters();
  }

  /**
   * Toggle category filter
   */
  toggleCategory(categoryId) {
    const index = this.filters.categories.indexOf(categoryId);
    if (index > -1) {
      this.filters.categories.splice(index, 1);
    } else {
      this.filters.categories.push(categoryId);
    }
    this.applyFilters();
  }

  /**
   * Set search query
   */
  setSearchQuery(query) {
    this.filters.searchQuery = query;
    this.applyFilters();
  }

  /**
   * Set sorting
   */
  setSorting(sortBy, sortOrder = 'desc') {
    this.filters.sortBy = sortBy;
    this.filters.sortOrder = sortOrder;
    this.applyFilters();
  }

  /**
   * Apply all filters
   */
  applyFilters() {
    const params = this.buildQueryParams();
    this.updateUI(params);
    this.saveCurrentFilters();
  }

  /**
   * Build query parameters from filters
   */
  buildQueryParams() {
    const params = new URLSearchParams();

    if (this.filters.dateRange.start) {
      params.append('start', this.filters.dateRange.start);
    }
    if (this.filters.dateRange.end) {
      params.append('end', this.filters.dateRange.end);
    }
    if (this.filters.categories.length > 0) {
      params.append('categories', this.filters.categories.join(','));
    }
    if (this.filters.amountRange.min !== null) {
      params.append('min_amount', this.filters.amountRange.min);
    }
    if (this.filters.amountRange.max !== null) {
      params.append('max_amount', this.filters.amountRange.max);
    }
    if (this.filters.searchQuery) {
      params.append('search', this.filters.searchQuery);
    }
    if (this.filters.sortBy) {
      params.append('sort', this.filters.sortBy);
      params.append('order', this.filters.sortOrder);
    }

    return params;
  }

  /**
   * Update UI with filtered results
   */
  updateUI(params) {
    // Trigger HTMX updates with new parameters
    const elements = document.querySelectorAll('[data-filter-target]');
    elements.forEach(element => {
      const url = element.getAttribute('hx-get');
      if (url) {
        const baseUrl = url.split('?')[0];
        element.setAttribute('hx-get', `${baseUrl}?${params.toString()}`);
        if (window.htmx) {
          htmx.trigger(element, 'refresh');
        }
      }
    });

    // Update filter count badge
    this.updateFilterCount();
  }

  /**
   * Get active filter count
   */
  getActiveFilterCount() {
    let count = 0;
    if (this.filters.dateRange.start || this.filters.dateRange.end) count++;
    if (this.filters.categories.length > 0) count++;
    if (this.filters.amountRange.min !== null || this.filters.amountRange.max !== null) count++;
    if (this.filters.searchQuery) count++;
    return count;
  }

  /**
   * Update filter count badge
   */
  updateFilterCount() {
    const badge = document.getElementById('filter-count-badge');
    const count = this.getActiveFilterCount();
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
  }

  /**
   * Save current filter set
   */
  saveFilterSet(name) {
    const filterSet = {
      name,
      filters: { ...this.filters },
      createdAt: new Date().toISOString()
    };

    this.savedFilters[name] = filterSet;
    localStorage.setItem('savedFilters', JSON.stringify(this.savedFilters));

    if (window.Toast) {
      Toast.success(`Filter set "${name}" saved`, 'Saved');
    }
  }

  /**
   * Load saved filter set
   */
  loadFilterSet(name) {
    const filterSet = this.savedFilters[name];
    if (filterSet) {
      this.filters = { ...filterSet.filters };
      this.applyFilters();

      if (window.Toast) {
        Toast.success(`Filter set "${name}" loaded`, 'Loaded');
      }
    }
  }

  /**
   * Delete saved filter set
   */
  deleteFilterSet(name) {
    delete this.savedFilters[name];
    localStorage.setItem('savedFilters', JSON.stringify(this.savedFilters));

    if (window.Toast) {
      Toast.success(`Filter set "${name}" deleted`, 'Deleted');
    }
  }

  /**
   * Load saved filters from localStorage
   */
  loadSavedFilters() {
    try {
      const saved = localStorage.getItem('savedFilters');
      return saved ? JSON.parse(saved) : {};
    } catch (error) {
      console.error('Error loading saved filters:', error);
      return {};
    }
  }

  /**
   * Save current filters to localStorage
   */
  saveCurrentFilters() {
    try {
      localStorage.setItem('currentFilters', JSON.stringify(this.filters));
    } catch (error) {
      console.error('Error saving current filters:', error);
    }
  }

  /**
   * Reset all filters
   */
  resetFilters() {
    this.filters = {
      dateRange: { start: null, end: null },
      categories: [],
      amountRange: { min: null, max: null },
      searchQuery: '',
      tags: [],
      sortBy: 'date',
      sortOrder: 'desc'
    };
    this.applyFilters();

    if (window.Toast) {
      Toast.info('All filters cleared', 'Filters Reset');
    }
  }

  /**
   * Get filter summary for display
   */
  getFilterSummary() {
    const summary = [];

    if (this.filters.dateRange.start || this.filters.dateRange.end) {
      summary.push(`Date: ${this.filters.dateRange.start || '∞'} - ${this.filters.dateRange.end || '∞'}`);
    }
    if (this.filters.categories.length > 0) {
      summary.push(`Categories: ${this.filters.categories.length} selected`);
    }
    if (this.filters.amountRange.min !== null || this.filters.amountRange.max !== null) {
      summary.push(`Amount: $${this.filters.amountRange.min || '0'} - $${this.filters.amountRange.max || '∞'}`);
    }
    if (this.filters.searchQuery) {
      summary.push(`Search: "${this.filters.searchQuery}"`);
    }

    return summary.join(' | ');
  }
}

// Initialize global advanced filters
window.advancedFilters = new AdvancedFilters();

// ==============================================
// BULK OPERATIONS
// ==============================================

class BulkOperations {
  constructor() {
    this.selectedItems = new Set();
    this.init();
  }

  init() {
    // Add event listeners for bulk selection
    document.addEventListener('change', (e) => {
      if (e.target.matches('.bulk-select-item')) {
        this.handleItemSelection(e.target);
      } else if (e.target.matches('.bulk-select-all')) {
        this.handleSelectAll(e.target);
      }
    });
  }

  /**
   * Handle individual item selection
   */
  handleItemSelection(checkbox) {
    const itemId = checkbox.value;
    if (checkbox.checked) {
      this.selectedItems.add(itemId);
    } else {
      this.selectedItems.delete(itemId);
    }
    this.updateBulkActionsUI();
  }

  /**
   * Handle select all checkbox
   */
  handleSelectAll(checkbox) {
    const items = document.querySelectorAll('.bulk-select-item');
    items.forEach(item => {
      item.checked = checkbox.checked;
      if (checkbox.checked) {
        this.selectedItems.add(item.value);
      } else {
        this.selectedItems.delete(item.value);
      }
    });
    this.updateBulkActionsUI();
  }

  /**
   * Update bulk actions UI
   */
  updateBulkActionsUI() {
    const count = this.selectedItems.size;
    const bulkBar = document.getElementById('bulk-actions-bar');
    const countElement = document.getElementById('bulk-selection-count');

    if (bulkBar) {
      bulkBar.style.display = count > 0 ? 'flex' : 'none';
    }
    if (countElement) {
      countElement.textContent = count;
    }
  }

  /**
   * Delete selected items
   */
  async deleteSelected() {
    if (this.selectedItems.size === 0) {
      Toast.warning('No items selected', 'Bulk Delete');
      return;
    }

    const confirmed = await ConfirmModal.show({
      type: 'danger',
      title: 'Delete Selected Items',
      message: `Are you sure you want to delete ${this.selectedItems.size} item(s)? This action cannot be undone.`,
      confirmText: 'Delete All',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    try {
      loadingManager.startLoading('body', { overlayText: 'Deleting items...' });

      const response = await fetch('/entries/bulk/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ids: Array.from(this.selectedItems)
        })
      });

      if (!response.ok) throw new Error('Bulk delete failed');

      const result = await response.json();

      Toast.success(`${result.deleted_count} item(s) deleted`, 'Bulk Delete Complete');

      this.clearSelection();
      this.refreshUI();
    } catch (error) {
      Toast.error('Failed to delete items', 'Bulk Delete Failed');
      errorBoundary.handleError(error);
    } finally {
      loadingManager.stopLoading('body');
    }
  }

  /**
   * Update category for selected items
   */
  async updateCategory(categoryId) {
    if (this.selectedItems.size === 0) {
      Toast.warning('No items selected', 'Bulk Update');
      return;
    }

    try {
      loadingManager.startLoading('body', { overlayText: 'Updating category...' });

      const response = await fetch('/entries/bulk/update-category', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ids: Array.from(this.selectedItems),
          category_id: categoryId
        })
      });

      if (!response.ok) throw new Error('Bulk update failed');

      const result = await response.json();

      Toast.success(`${result.updated_count} item(s) updated`, 'Bulk Update Complete');

      this.clearSelection();
      this.refreshUI();
    } catch (error) {
      Toast.error('Failed to update items', 'Bulk Update Failed');
      errorBoundary.handleError(error);
    } finally {
      loadingManager.stopLoading('body');
    }
  }

  /**
   * Export selected items
   */
  async exportSelected(format = 'csv') {
    if (this.selectedItems.size === 0) {
      Toast.warning('No items selected', 'Bulk Export');
      return;
    }

    try {
      const params = new URLSearchParams({
        ids: Array.from(this.selectedItems).join(','),
        format: format
      });

      window.open(`/entries/bulk/export?${params.toString()}`, '_blank');

      Toast.success(`Exporting ${this.selectedItems.size} item(s)`, 'Export Started');
    } catch (error) {
      Toast.error('Failed to export items', 'Export Failed');
      errorBoundary.handleError(error);
    }
  }

  /**
   * Clear selection
   */
  clearSelection() {
    this.selectedItems.clear();
    document.querySelectorAll('.bulk-select-item, .bulk-select-all').forEach(checkbox => {
      checkbox.checked = false;
    });
    this.updateBulkActionsUI();
  }

  /**
   * Refresh UI after bulk operation
   */
  refreshUI() {
    // Trigger HTMX refresh for data lists
    const refreshTargets = document.querySelectorAll('[data-refresh-on-bulk]');
    refreshTargets.forEach(target => {
      if (window.htmx) {
        htmx.trigger(target, 'refresh');
      }
    });
  }

  /**
   * Get selected count
   */
  getSelectedCount() {
    return this.selectedItems.size;
  }
}

// Initialize global bulk operations
window.bulkOperations = new BulkOperations();

// ==============================================
// ADVANCED SEARCH
// ==============================================

class AdvancedSearch {
  constructor() {
    this.searchHistory = this.loadSearchHistory();
    this.searchSuggestions = [];
  }

  /**
   * Perform search with debouncing
   */
  search(query, options = {}) {
    const {
      debounce = 300,
      minLength = 2,
      onResults = null
    } = options;

    if (query.length < minLength) return;

    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(async () => {
      const results = await this.performSearch(query);

      if (onResults) {
        onResults(results);
      }

      this.addToHistory(query);
    }, debounce);
  }

  /**
   * Perform actual search
   */
  async performSearch(query) {
    try {
      const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');

      const results = await response.json();
      return results;
    } catch (error) {
      errorBoundary.handleError(error);
      return [];
    }
  }

  /**
   * Get search suggestions
   */
  async getSuggestions(query) {
    if (query.length < 2) return [];

    try {
      const response = await fetch(`/search/suggestions?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Failed to get suggestions');

      const suggestions = await response.json();
      this.searchSuggestions = suggestions;
      return suggestions;
    } catch (error) {
      errorBoundary.handleError(error);
      return [];
    }
  }

  /**
   * Add query to search history
   */
  addToHistory(query) {
    if (!query) return;

    // Add to beginning, remove duplicates, limit to 10
    this.searchHistory = [
      query,
      ...this.searchHistory.filter(q => q !== query)
    ].slice(0, 10);

    localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
  }

  /**
   * Load search history
   */
  loadSearchHistory() {
    try {
      const history = localStorage.getItem('searchHistory');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      return [];
    }
  }

  /**
   * Clear search history
   */
  clearHistory() {
    this.searchHistory = [];
    localStorage.removeItem('searchHistory');
    Toast.info('Search history cleared', 'Cleared');
  }

  /**
   * Get search history
   */
  getHistory() {
    return this.searchHistory;
  }
}

// Initialize global advanced search
window.advancedSearch = new AdvancedSearch();

// ==============================================
// DATA VALIDATION
// ==============================================

class DataValidator {
  /**
   * Validate expense entry
   */
  static validateExpenseEntry(data) {
    const errors = [];

    // Amount validation
    if (!data.amount || data.amount <= 0) {
      errors.push('Amount must be greater than 0');
    }
    if (data.amount > 1000000) {
      errors.push('Amount exceeds maximum limit');
    }

    // Description validation
    if (!data.description || data.description.trim().length === 0) {
      errors.push('Description is required');
    }
    if (data.description && data.description.length > 500) {
      errors.push('Description is too long (max 500 characters)');
    }

    // Category validation
    if (!data.category_id) {
      errors.push('Category is required');
    }

    // Date validation
    if (!data.date) {
      errors.push('Date is required');
    } else {
      const date = new Date(data.date);
      if (isNaN(date.getTime())) {
        errors.push('Invalid date format');
      }
      if (date > new Date()) {
        errors.push('Date cannot be in the future');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Sanitize user input
   */
  static sanitizeInput(input) {
    if (typeof input !== 'string') return input;

    // Remove HTML tags
    const doc = new DOMParser().parseFromString(input, 'text/html');
    let sanitized = doc.body.textContent || '';

    // Trim whitespace
    sanitized = sanitized.trim();

    // Remove multiple spaces
    sanitized = sanitized.replace(/\s+/g, ' ');

    return sanitized;
  }

  /**
   * Validate amount input
   */
  static validateAmount(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return { isValid: false, error: 'Invalid number' };
    if (num <= 0) return { isValid: false, error: 'Amount must be positive' };
    if (num > 1000000) return { isValid: false, error: 'Amount too large' };
    return { isValid: true, value: num };
  }

  /**
   * Validate date input
   */
  static validateDate(dateString) {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return { isValid: false, error: 'Invalid date' };
    }
    if (date > new Date()) {
      return { isValid: false, error: 'Date cannot be in future' };
    }
    return { isValid: true, value: date };
  }
}

window.DataValidator = DataValidator;

// ==============================================
// KEYBOARD SHORTCUTS
// ==============================================

class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.enabled = true;
    this.init();
  }

  init() {
    document.addEventListener('keydown', (e) => {
      if (!this.enabled) return;
      if (this.isInputElement(e.target)) return;

      const key = this.getKeyCombo(e);
      const handler = this.shortcuts.get(key);

      if (handler) {
        e.preventDefault();
        handler(e);
      }
    });

    // Register default shortcuts
    this.registerDefaults();
  }

  /**
   * Check if element is an input
   */
  isInputElement(element) {
    return element.tagName === 'INPUT' ||
           element.tagName === 'TEXTAREA' ||
           element.tagName === 'SELECT' ||
           element.isContentEditable;
  }

  /**
   * Get key combination string
   */
  getKeyCombo(event) {
    const parts = [];
    if (event.ctrlKey || event.metaKey) parts.push('ctrl');
    if (event.shiftKey) parts.push('shift');
    if (event.altKey) parts.push('alt');
    parts.push(event.key.toLowerCase());
    return parts.join('+');
  }

  /**
   * Register a keyboard shortcut
   */
  register(keyCombo, handler, description = '') {
    this.shortcuts.set(keyCombo, handler);
  }

  /**
   * Unregister a keyboard shortcut
   */
  unregister(keyCombo) {
    this.shortcuts.delete(keyCombo);
  }

  /**
   * Enable/disable shortcuts
   */
  setEnabled(enabled) {
    this.enabled = enabled;
  }

  /**
   * Register default shortcuts
   */
  registerDefaults() {
    // Search: Ctrl/Cmd + K
    this.register('ctrl+k', () => {
      const searchInput = document.getElementById('global-search');
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    }, 'Open search');

    // New entry: Ctrl/Cmd + N
    this.register('ctrl+n', () => {
      window.location.href = '/entries/new';
    }, 'New entry');

    // Help: ?
    this.register('?', () => {
      this.showShortcutsHelp();
    }, 'Show keyboard shortcuts');

    // Escape: Close modals
    this.register('escape', () => {
      const modal = document.querySelector('.modal-overlay');
      if (modal) {
        modal.querySelector('[data-action="cancel"]')?.click();
      }
    }, 'Close modal');
  }

  /**
   * Show keyboard shortcuts help
   */
  showShortcutsHelp() {
    const shortcuts = [
      { key: 'Ctrl/Cmd + K', description: 'Open search' },
      { key: 'Ctrl/Cmd + N', description: 'New entry' },
      { key: '?', description: 'Show this help' },
      { key: 'Escape', description: 'Close modal' },
      { key: 'Tab', description: 'Navigate between elements' }
    ];

    const html = `
      <div style="max-width: 400px;">
        <h3 style="margin-top: 0;">Keyboard Shortcuts</h3>
        <div style="display: grid; gap: 12px;">
          ${shortcuts.map(s => `
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <kbd style="
                background: rgba(255,255,255,0.1);
                padding: 4px 8px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 0.875rem;
              ">${s.key}</kbd>
              <span style="margin-left: 16px; flex: 1;">${s.description}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Show in a modal or toast
    if (window.Toast) {
      Toast.info(html, 'Keyboard Shortcuts', { duration: 10000 });
    }
  }
}

// Initialize keyboard shortcuts
window.keyboardShortcuts = new KeyboardShortcuts();

// ==============================================
// CONSOLE MESSAGES
// ==============================================

if (window.errorBoundary?.isDevelopment()) {
  console.log(
    '%cAdvanced Features Active',
    'color: #4da3ff; font-weight: bold; font-size: 14px;'
  );
  console.log('Available features:', {
    advancedFilters: window.advancedFilters,
    bulkOperations: window.bulkOperations,
    advancedSearch: window.advancedSearch,
    DataValidator: window.DataValidator,
    keyboardShortcuts: window.keyboardShortcuts
  });
}
