/* ============================================
   Library Management System - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ---------- DataTables Initialization ----------
  initDataTables();

  // ---------- Sidebar Active Link ----------
  highlightActiveLink();

  // ---------- Mobile Sidebar Toggle ----------
  initSidebarToggle();

  // ---------- Auto-dismiss Alerts ----------
  autoDismissAlerts();

  // ---------- Delete Confirmation ----------
  initDeleteConfirmation();

  // ---------- Password Visibility Toggle ----------
  initPasswordToggle();

  // ---------- Form Validation ----------
  initFormValidation();

  // ---------- Tooltip Init ----------
  initTooltips();

  // ---------- Filter Buttons ----------
  initFilterButtons();
});


/* ========== DataTables ========== */
function initDataTables() {
  if ($.fn.DataTable) {
    $('.data-table').each(function () {
      if (!$.fn.DataTable.isDataTable(this)) {
        $(this).DataTable({
          responsive: true,
          pageLength: 10,
          lengthMenu: [5, 10, 25, 50, 100],
          language: {
            search: '',
            searchPlaceholder: 'Search records...',
            lengthMenu: 'Show _MENU_ entries',
            info: 'Showing _START_ to _END_ of _TOTAL_ records',
            infoEmpty: 'No records found',
            emptyTable: 'No data available',
            paginate: {
              first: '<i class="fas fa-angle-double-left"></i>',
              last: '<i class="fas fa-angle-double-right"></i>',
              next: '<i class="fas fa-angle-right"></i>',
              previous: '<i class="fas fa-angle-left"></i>'
            }
          },
          dom: '<"datatable-top"lf>rt<"datatable-bottom"ip>',
          drawCallback: function () {
            // Re-init tooltips after table redraw
            initTooltips();
          }
        });
      }
    });
  }
}


/* ========== Sidebar Active Link ========== */
function highlightActiveLink() {
  var currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href && currentPath.startsWith(href) && href !== '/') {
      link.classList.add('active');
    } else if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    }
  });
}


/* ========== Mobile Sidebar Toggle ========== */
function initSidebarToggle() {
  var toggle = document.getElementById('sidebarToggle');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebarOverlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      if (overlay) overlay.classList.toggle('show');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', function () {
      if (sidebar) sidebar.classList.remove('show');
      overlay.classList.remove('show');
    });
  }
}


/* ========== Auto-dismiss Alerts ========== */
function autoDismissAlerts() {
  var alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function () {
          bsAlert.close();
        }, 500);
      }
    }, 5000);
  });
}


/* ========== Delete Confirmation ========== */
function initDeleteConfirmation() {
  var deleteModal = document.getElementById('deleteConfirmModal');
  if (!deleteModal) return;

  deleteModal.addEventListener('show.bs.modal', function (event) {
    var button = event.relatedTarget;
    var itemName = button.getAttribute('data-item-name') || 'this item';
    var deleteUrl = button.getAttribute('data-delete-url') || '#';

    var modalItemName = deleteModal.querySelector('#deleteItemName');
    var modalForm = deleteModal.querySelector('#deleteForm');

    if (modalItemName) modalItemName.textContent = itemName;
    if (modalForm) modalForm.setAttribute('action', deleteUrl);
  });
}

// Standalone confirm delete for inline usage
function confirmDelete(url, itemName) {
  var modal = document.getElementById('deleteConfirmModal');
  if (modal) {
    var modalItemName = modal.querySelector('#deleteItemName');
    var modalForm = modal.querySelector('#deleteForm');
    if (modalItemName) modalItemName.textContent = itemName || 'this item';
    if (modalForm) modalForm.setAttribute('action', url);
    var bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  } else {
    if (confirm('Are you sure you want to delete ' + (itemName || 'this item') + '?')) {
      window.location.href = url;
    }
  }
}


/* ========== Password Visibility Toggle ========== */
function initPasswordToggle() {
  var toggleBtns = document.querySelectorAll('.password-toggle');
  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = this.closest('.position-relative').querySelector('input');
      var icon = this.querySelector('i');
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          input.type = 'password';
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }
    });
  });
}


/* ========== Form Validation ========== */
function initFormValidation() {
  var forms = document.querySelectorAll('.needs-validation');
  forms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });
}


/* ========== Tooltips ========== */
function initTooltips() {
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });
}


/* ========== Filter Buttons (Issues page) ========== */
function initFilterButtons() {
  document.querySelectorAll('.filter-btn[data-filter]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = this.getAttribute('data-filter');

      // Update active state
      document.querySelectorAll('.filter-btn[data-filter]').forEach(function (b) {
        b.classList.remove('active');
      });
      this.classList.add('active');

      // Filter table rows
      var rows = document.querySelectorAll('.filterable-row');
      rows.forEach(function (row) {
        if (filter === 'all') {
          row.style.display = '';
        } else {
          var status = row.getAttribute('data-status');
          row.style.display = (status === filter) ? '' : 'none';
        }
      });
    });
  });
}


/* ========== Dashboard Charts ========== */
function renderCategoryChart(labels, data) {
  var ctx = document.getElementById('categoryChart');
  if (!ctx) return null;

  var colors = [
    '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
    '#f97316', '#eab308', '#22c55e', '#14b8a6',
    '#06b6d4', '#3b82f6', '#a855f7', '#d946ef'
  ];

  return new Chart(ctx.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 8,
            font: {
              family: "'Inter', sans-serif",
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { family: "'Inter', sans-serif", weight: '600' },
          bodyFont: { family: "'Inter', sans-serif" },
          padding: 12,
          cornerRadius: 8,
          displayColors: true
        }
      }
    }
  });
}

function renderTrendsChart(labels, issueData, returnData) {
  var ctx = document.getElementById('trendsChart');
  if (!ctx) return null;

  return new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Issued',
          data: issueData,
          backgroundColor: 'rgba(99, 102, 241, 0.8)',
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 18
        },
        {
          label: 'Returned',
          data: returnData,
          backgroundColor: 'rgba(16, 185, 129, 0.8)',
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 18
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: "'Inter', sans-serif", size: 11 }
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0,0,0,0.04)',
            drawBorder: false
          },
          ticks: {
            font: { family: "'Inter', sans-serif", size: 11 },
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 8,
            font: {
              family: "'Inter', sans-serif",
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { family: "'Inter', sans-serif", weight: '600' },
          bodyFont: { family: "'Inter', sans-serif" },
          padding: 12,
          cornerRadius: 8
        }
      }
    }
  });
}


/* ========== Utility Functions ========== */
function showToast(message, type) {
  type = type || 'info';
  var container = document.querySelector('.content-wrapper');
  if (!container) return;

  var alertDiv = document.createElement('div');
  alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
  alertDiv.setAttribute('role', 'alert');
  alertDiv.innerHTML =
    '<i class="fas fa-' + (type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle') + '"></i>' +
    message +
    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

  container.insertBefore(alertDiv, container.firstChild);

  setTimeout(function () {
    alertDiv.style.transition = 'opacity 0.5s ease';
    alertDiv.style.opacity = '0';
    setTimeout(function () { alertDiv.remove(); }, 500);
  }, 4000);
}
