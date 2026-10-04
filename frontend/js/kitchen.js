// Lógica do Módulo KDS / Cozinha - Nexa Gestão

document.addEventListener('DOMContentLoaded', function() {
    loadKitchenOrders();

    // Configurar atualização automática do display a cada 10 segundos (10000 ms)
    setInterval(function() {
        autoRefreshKitchenDisplay();
    }, 10000);
});

function openKitchenModal() {
    var modal = document.getElementById('kitchenModal');
    if (modal) modal.classList.add('open');
}

function closeKitchenModal() {
    var modal = document.getElementById('kitchenModal');
    var form = document.getElementById('newKitchenForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function loadKitchenOrders() {
    updateKitchenMetrics();
}

// Função executada automaticamente a cada 10 segundos
function autoRefreshKitchenDisplay() {
    updateKitchenMetrics();
    
    // Efeito visual opcional na barra de título para indicar sincronização do KDS
    var titleEl = document.querySelector('header h1');
    if (titleEl) {
        var originalText = titleEl.innerText;
        titleEl.innerText = '📺 Display de Cozinha (KDS) — Sincronizado';
        setTimeout(function() {
            titleEl.innerText = originalText;
        }, 2000);
    }
}

function handleCreateKitchenOrder(event) {
    event.preventDefault();

    var orderNumInput = document.getElementById('kdsOrderNumInput');
    var tableInput = document.getElementById('kdsTableInput');
    var itemsInput = document.getElementById('kdsItemsInput');
    var statusInput = document.getElementById('kdsStatusInput');

    if (!orderNumInput || !tableInput || !itemsInput || !statusInput) return;

    var orderNum = orderNumInput.value.trim();
    var table = tableInput.value.trim();
    var items = itemsInput.value.trim();
    var status = statusInput.value; // 'preparando' ou 'pronto'

    if (!orderNum || !table || !items) return;

    var tbody = document.getElementById('kitchenTableBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');
    var isReady = (status === 'pronto');
    var badgeClass = isReady ? 'badge-status pronto' : 'badge-status preparando';
    var badgeText = isReady ? 'Pronto' : 'Em Preparo';
    var toggleBtnText = isReady ? 'Marcar Preparando' : 'Marcar Pronto';

    newRow.innerHTML = '<td><strong>' + orderNum + '</strong></td>' +
        '<td>' + table + '</td>' +
        '<td>' + items + '</td>' +
        '<td><span class="' + badgeClass + '">' + badgeText + '</span></td>' +
        '<td style="text-align: right;">' +
            '<button class="btn-action-kds" onclick="toggleOrderStatus(this)">' + toggleBtnText + '</button>' +
            '<button class="btn-delete-kds" onclick="deleteKitchenOrder(this)">Excluir</button>' +
        '</td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    updateKitchenMetrics();
    closeKitchenModal();
}

function toggleOrderStatus(buttonElement) {
    var row = buttonElement.closest('tr');
    if (!row) return;

    var badgeSpan = row.querySelector('.badge-status');
    if (!badgeSpan) return;

    if (badgeSpan.classList.contains('preparando')) {
        badgeSpan.className = 'badge-status pronto';
        badgeSpan.innerText = 'Pronto';
        buttonElement.innerText = 'Marcar Preparando';
    } else {
        badgeSpan.className = 'badge-status preparando';
        badgeSpan.innerText = 'Em Preparo';
        buttonElement.innerText = 'Marcar Pronto';
    }

    updateKitchenMetrics();
}

function deleteKitchenOrder(buttonElement) {
    if (confirm('Tem certeza de que deseja remover este pedido do KDS?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('kitchenTableBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-row-state">Nenhum pedido ativo na cozinha no momento.</td></tr>';
        }

        updateKitchenMetrics();
    }
}

function updateKitchenMetrics() {
    var tbody = document.getElementById('kitchenTableBody');
    if (!tbody) return;

    var rows = tbody.querySelectorAll('tr');
    var hasEmpty = tbody.querySelector('.empty-row-state');

    var preparingCount = 0;
    var readyCount = 0;
    var totalQueue = 0;

    if (!hasEmpty) {
        totalQueue = rows.length;

        for (var i = 0; i < rows.length; i++) {
            var badgeSpan = rows[i].querySelector('.badge-status');
            if (badgeSpan) {
                if (badgeSpan.classList.contains('pronto')) {
                    readyCount++;
                } else {
                    preparingCount++;
                }
            }
        }
    }

    var prepEl = document.getElementById('metricPreparingCount');
    var readyEl = document.getElementById('metricReadyCount');
    var totalEl = document.getElementById('metricTotalQueue');

    if (prepEl) prepEl.innerText = preparingCount;
    if (readyEl) readyEl.innerText = readyCount;
    if (totalEl) totalEl.innerText = totalQueue;
}