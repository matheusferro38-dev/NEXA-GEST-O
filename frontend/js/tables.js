// Lógica do Módulo de Mesas e Pedidos - Nexa Gestão

document.addEventListener('DOMContentLoaded', function() {
    loadTables();
});

function openTableModal() {
    var modal = document.getElementById('tableModal');
    if (modal) modal.classList.add('open');
}

function closeTableModal() {
    var modal = document.getElementById('tableModal');
    var form = document.getElementById('newTableForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function loadTables() {
    updateTableMetrics();
}

function handleCreateTable(event) {
    event.preventDefault();

    var nameInput = document.getElementById('tableNameInput');
    var clientInput = document.getElementById('tableClientInput');
    var statusInput = document.getElementById('tableStatusInput');
    var consumptionInput = document.getElementById('tableConsumptionInput');

    if (!nameInput || !clientInput || !statusInput || !consumptionInput) return;

    var tableName = nameInput.value.trim();
    var clientName = clientInput.value.trim();
    var status = statusInput.value; // 'ocupada' ou 'livre'
    var consumption = parseFloat(consumptionInput.value) || 0;

    if (!tableName || !clientName || consumption < 0) return;

    var tbody = document.getElementById('tablesTableBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');
    var isOccupied = (status === 'ocupada');
    var badgeClass = isOccupied ? 'badge-status ocupada' : 'badge-status livre';
    var badgeText = isOccupied ? 'Ocupada' : 'Livre';
    var formattedConsumption = 'R$ ' + consumption.toFixed(2).replace('.', ',');

    newRow.innerHTML = '<td><strong>' + tableName + '</strong></td>' +
        '<td>' + clientName + '</td>' +
        '<td><span class="' + badgeClass + '">' + badgeText + '</span></td>' +
        '<td style="font-weight: 700; color: ' + (isOccupied ? 'var(--color-text)' : 'var(--color-text-muted)') + ';">' + formattedConsumption + '</td>' +
        '<td style="text-align: right;"><button class="btn-delete-table" onclick="deleteTable(this)">Excluir</button></td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    updateTableMetrics();
    closeTableModal();
}

function deleteTable(buttonElement) {
    if (confirm('Tem certeza de que deseja excluir este registo de mesa?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('tablesTableBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-row-state">Nenhuma mesa ou comanda aberta no momento.</td></tr>';
        }

        updateTableMetrics();
    }
}

function updateTableMetrics() {
    var tbody = document.getElementById('tablesTableBody');
    if (!tbody) return;

    var rows = tbody.querySelectorAll('tr');
    var hasEmpty = tbody.querySelector('.empty-row-state');

    var totalTables = 0;
    var occupiedTables = 0;
    var totalConsumption = 0;

    if (!hasEmpty) {
        totalTables = rows.length;

        for (var i = 0; i < rows.length; i++) {
            var badgeSpan = rows[i].querySelector('.badge-status');
            var consCell = rows[i].querySelector('td:nth-last-child(2)');

            if (badgeSpan && badgeSpan.classList.contains('ocupada')) {
                occupiedTables++;
            }

            if (consCell) {
                var cleanNum = consCell.innerText.replace(/[^0-9,-]/g, '').replace('.', '').replace(',', '.');
                var num = parseFloat(cleanNum) || 0;
                totalConsumption += num;
            }
        }
    }

    var totalEl = document.getElementById('metricTotalTables');
    var occEl = document.getElementById('metricOccupiedTables');
    var consEl = document.getElementById('metricTotalConsumption');

    if (totalEl) totalEl.innerText = totalTables;
    if (occEl) occEl.innerText = occupiedTables;
    if (consEl) consEl.innerText = 'R$ ' + totalConsumption.toFixed(2).replace('.', ',');
}

function exportTableReport() {
    var tbody = document.getElementById('tablesTableBody');
    var rows = tbody ? tbody.querySelectorAll('tr') : [];
    
    if (rows.length === 0 || tbody.querySelector('.empty-row-state')) {
        alert('Não existem mesas ou comandas registadas para exportar.');
        return;
    }

    alert('Relatório de mesas exportado com sucesso!');
}