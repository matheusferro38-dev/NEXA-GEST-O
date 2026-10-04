// Lógica do Módulo Dashboard / Visão Geral - Nexa Gestão

document.addEventListener('DOMContentLoaded', function() {
    refreshDashboard();
});

function openActivityModal() {
    var modal = document.getElementById('activityModal');
    if (modal) modal.classList.add('open');
}

function closeActivityModal() {
    var modal = document.getElementById('activityModal');
    var form = document.getElementById('newActivityForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function refreshDashboard() {
    updateDashboardMetrics();
}

function handleCreateActivity(event) {
    event.preventDefault();

    var timeInput = document.getElementById('actTimeInput');
    var categoryInput = document.getElementById('actCategoryInput');
    var descInput = document.getElementById('actDescInput');

    if (!timeInput || !categoryInput || !descInput) return;

    var time = timeInput.value.trim();
    var category = categoryInput.value.trim();
    var description = descInput.value.trim();

    if (!time || !category || !description) return;

    var tbody = document.getElementById('dashboardActivityBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');

    newRow.innerHTML = '<td><strong>' + time + '</strong></td>' +
        '<td><span class="badge-activity">' + category + '</span></td>' +
        '<td>' + description + '</td>' +
        '<td style="text-align: right;"><button class="btn-delete-activity" onclick="deleteActivity(this)">Excluir</button></td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    closeActivityModal();
}

function deleteActivity(buttonElement) {
    if (confirm('Tem certeza de que deseja excluir este apontamento?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('dashboardActivityBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-row-state">Nenhum apontamento registado no momento.</td></tr>';
        }
    }
}

function updateDashboardMetrics() {
    // Como os dados são dinâmicos e limpos, iniciais a zero por defeito
    var revenueEl = document.getElementById('dashMetricRevenue');
    var tablesEl = document.getElementById('dashMetricTables');
    var kitchenEl = document.getElementById('dashMetricKitchen');
    var employeesEl = document.getElementById('dashMetricEmployees');

    if (revenueEl) revenueEl.innerText = 'R$ 0,00';
    if (tablesEl) tablesEl.innerText = '0';
    if (kitchenEl) kitchenEl.innerText = '0';
    if (employeesEl) employeesEl.innerText = '0';
}