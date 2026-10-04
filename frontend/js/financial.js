// Lógica do Módulo Financeiro - Nexa Gestão (Inclusão e Exclusão Dinâmica)

document.addEventListener('DOMContentLoaded', function() {
    loadTransactions();
});

function openTransactionModal() {
    var modal = document.getElementById('transactionModal');
    if (modal) modal.classList.add('open');
}

function closeTransactionModal() {
    var modal = document.getElementById('transactionModal');
    var form = document.getElementById('newTransactionForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function loadTransactions() {
    updateFinancialMetrics(0, 0);
}

function handleCreateTransaction(event) {
    event.preventDefault();

    var descInput = document.getElementById('transDescInput');
    var typeInput = document.getElementById('transTypeInput');
    var catInput = document.getElementById('transCategoryInput');
    var valInput = document.getElementById('transValueInput');

    if (!descInput || !typeInput || !catInput || !valInput) return;

    var description = descInput.value.trim();
    var type = typeInput.value; // 'receita' ou 'despesa'
    var category = catInput.value.trim();
    var amount = parseFloat(valInput.value) || 0;

    if (!description || amount <= 0) return;

    var today = new Date();
    var day = String(today.getDate()).padStart(2, '0');
    var month = String(today.getMonth() + 1).padStart(2, '0');
    var year = today.getFullYear();
    var formattedDate = day + '/' + month + '/' + year;

    var tbody = document.getElementById('transactionsTableBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');
    var isRevenue = (type === 'receita');
    var badgeClass = isRevenue ? 'badge-trans receita' : 'badge-trans despesa';
    var badgeText = isRevenue ? 'Receita' : 'Despesa';
    var formattedAmount = (isRevenue ? '+ R$ ' : '- R$ ') + amount.toFixed(2).replace('.', ',');
    var amountColor = isRevenue ? 'var(--color-success)' : 'var(--color-danger)';

    newRow.innerHTML = '<td>' + formattedDate + '</td>' +
        '<td><strong>' + description + '</strong></td>' +
        '<td>' + category + '</td>' +
        '<td><span class="' + badgeClass + '">' + badgeText + '</span></td>' +
        '<td style="color: ' + amountColor + '; font-weight: 700;">' + formattedAmount + '</td>' +
        '<td style="text-align: right;"><button class="btn-delete-trans" onclick="deleteTransaction(this)">Excluir</button></td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    recalculateMetricsFromTable();
    closeTransactionModal();
}

function deleteTransaction(buttonElement) {
    if (confirm('Tem certeza de que deseja excluir esta transação?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('transactionsTableBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-row-state">Nenhuma transação registada no período.</td></tr>';
            updateFinancialMetrics(0, 0);
        } else {
            recalculateMetricsFromTable();
        }
    }
}

function recalculateMetricsFromTable() {
    var tbody = document.getElementById('transactionsTableBody');
    if (!tbody) return;

    var rows = tbody.querySelectorAll('tr');
    var totalRevenue = 0;
    var totalExpenses = 0;

    for (var i = 0; i < rows.length; i++) {
        // Ignorar se for linha de estado vazio
        if (rows[i].querySelector('.empty-row-state')) continue;

        var valCell = rows[i].querySelector('td:nth-last-child(2)');
        if (!valCell) continue;

        var textValue = valCell.innerText.trim();
        var isRev = textValue.indexOf('+') !== -1;
        
        var cleanNum = textValue.replace(/[^0-9,-]/g, '').replace('.', '').replace(',', '.');
        var num = parseFloat(cleanNum) || 0;

        if (isRev) {
            totalRevenue += num;
        } else {
            totalExpenses += num;
        }
    }

    updateFinancialMetrics(totalRevenue, totalExpenses);
}

function updateFinancialMetrics(revenue, expenses) {
    var revEl = document.getElementById('metricTotalRevenue');
    var expEl = document.getElementById('metricTotalExpenses');
    var netEl = document.getElementById('metricNetBalance');

    if (revEl) revEl.innerText = 'R$ ' + revenue.toFixed(2).replace('.', ',');
    if (expEl) expEl.innerText = 'R$ ' + expenses.toFixed(2).replace('.', ',');
    
    if (netEl) {
        var net = revenue - expenses;
        netEl.innerText = 'R$ ' + net.toFixed(2).replace('.', ',');
    }
}

function exportFinancialReport() {
    var tbody = document.getElementById('transactionsTableBody');
    var rows = tbody ? tbody.querySelectorAll('tr') : [];
    
    if (rows.length === 0 || tbody.querySelector('.empty-row-state')) {
        alert('Não existem dados financeiros registados para exportar.');
        return;
    }

    alert('Relatório financeiro exportado com sucesso!');
}