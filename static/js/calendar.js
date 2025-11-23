/**
 * Calendar View JavaScript
 * Phase 26: Calendar View Implementation
 */

(function() {
  'use strict';

  /**
   * Show date detail modal
   */
  window.showDateDetail = function(dateStr) {
    const modal = new bootstrap.Modal(document.getElementById('dateDetailModal'));
    const modalBody = document.getElementById('dateDetailContent');

    // Show loading state
    modalBody.innerHTML = `
      <div class="text-center py-4">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;

    // Show modal
    modal.show();

    // Fetch date details
    fetch(`/calendar/date/${dateStr}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load date details');
        }
        return response.text();
      })
      .then(html => {
        modalBody.innerHTML = html;
      })
      .catch(error => {
        console.error('Error loading date details:', error);
        modalBody.innerHTML = `
          <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i>
            Failed to load date details. Please try again.
          </div>
        `;
      });
  };

  /**
   * Handle keyboard navigation on calendar dates
   */
  document.addEventListener('DOMContentLoaded', function() {
    const calendarDates = document.querySelectorAll('.calendar-date.has-entries');

    calendarDates.forEach(date => {
      // Handle Enter key
      date.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const dateStr = this.getAttribute('data-date');
          if (dateStr) {
            showDateDetail(dateStr);
          }
        }
      });
    });

    // Keyboard navigation between dates (arrow keys)
    let currentFocusIndex = -1;
    const hasEntriesDates = Array.from(calendarDates);

    document.addEventListener('keydown', function(e) {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
        return;
      }

      if (document.activeElement.classList.contains('calendar-date')) {
        e.preventDefault();

        currentFocusIndex = hasEntriesDates.indexOf(document.activeElement);

        switch(e.key) {
          case 'ArrowLeft':
            currentFocusIndex = Math.max(0, currentFocusIndex - 1);
            break;
          case 'ArrowRight':
            currentFocusIndex = Math.min(hasEntriesDates.length - 1, currentFocusIndex + 1);
            break;
          case 'ArrowUp':
            currentFocusIndex = Math.max(0, currentFocusIndex - 7);
            break;
          case 'ArrowDown':
            currentFocusIndex = Math.min(hasEntriesDates.length - 1, currentFocusIndex + 7);
            break;
        }

        if (hasEntriesDates[currentFocusIndex]) {
          hasEntriesDates[currentFocusIndex].focus();
        }
      }
    });
  });

  /**
   * Mobile tooltip handling
   * On mobile, tap to show tooltip instead of hover
   */
  if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
    document.addEventListener('DOMContentLoaded', function() {
      const calendarDates = document.querySelectorAll('.calendar-date.has-entries');

      calendarDates.forEach(date => {
        let tooltipVisible = false;
        const tooltip = date.querySelector('.date-tooltip');

        if (!tooltip) return;

        date.addEventListener('touchstart', function(e) {
          if (!tooltipVisible) {
            e.preventDefault();
            e.stopPropagation();

            // Hide all other tooltips
            document.querySelectorAll('.date-tooltip').forEach(t => {
              t.style.opacity = '0';
              t.style.visibility = 'hidden';
            });

            // Show this tooltip
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
            tooltipVisible = true;

            // Hide after 3 seconds or on next touch
            setTimeout(() => {
              if (tooltipVisible) {
                tooltip.style.opacity = '0';
                tooltip.style.visibility = 'hidden';
                tooltipVisible = false;
              }
            }, 3000);
          }
        });

        // Double tap to open modal
        let lastTap = 0;
        date.addEventListener('touchend', function(e) {
          const currentTime = new Date().getTime();
          const tapLength = currentTime - lastTap;

          if (tapLength < 500 && tapLength > 0) {
            // Double tap detected
            const dateStr = this.getAttribute('data-date');
            if (dateStr) {
              showDateDetail(dateStr);
            }
          }

          lastTap = currentTime;
        });
      });

      // Hide tooltips when touching outside
      document.addEventListener('touchstart', function(e) {
        if (!e.target.closest('.calendar-date')) {
          document.querySelectorAll('.date-tooltip').forEach(tooltip => {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
          });
        }
      });
    });
  }

  /**
   * Add smooth scrolling to calendar on month change
   */
  window.addEventListener('load', function() {
    // Check if there's a hash or came from navigation
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('year') || urlParams.has('month')) {
      const calendarGrid = document.querySelector('.calendar-grid-wrapper');
      if (calendarGrid) {
        calendarGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });

  /**
   * Highlight today's date on load
   */
  document.addEventListener('DOMContentLoaded', function() {
    const todayDate = document.querySelector('.calendar-date.today');
    if (todayDate) {
      // Add a subtle pulse animation to today's date
      todayDate.style.animation = 'pulse 2s ease-in-out';

      // Remove animation after it completes
      setTimeout(() => {
        todayDate.style.animation = '';
      }, 2000);
    }
  });

  /**
   * Add pulse animation for today
   */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.05);
      }
    }
  `;
  document.head.appendChild(style);

  console.log('[Calendar] Initialized');
})();
