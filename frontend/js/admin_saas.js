// Lógica do Painel SaaS - Nexa Gestão

// Função para abrir o modal de novo estabelecimento
function openModal() {
    var modal = document.getElementById('tenantModal');
    if (modal) modal.classList.add('open');
}

// Função para fechar o modal
function closeModal() {
    var modal = document.getElementById('tenantModal');
    var form = document.getElementById('newTenantForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

// Função para gerir o inquilino (botão Gerir)
function viewTenant() {
    alert('A carregar painel de gestão do estabelecimento...');
}

// Função para remover um estabelecimento com atualização segura de métricas
function removeTenant(buttonElement, planPrice) {
    if (confirm('Tem certeza de que deseja remover este estabelecimento?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
            updateMetrics(-1, -planPrice);

            var tbody = document.getElementById('saasTableBody');
            if (tbody && tbody.querySelectorAll('tr').length === 0) {
                tbody.innerHTML = '<tr id="emptyRow"><td colspan="5"><div class="empty-state"><p style="font-size: 15px; font-weight: 600; margin-bottom: 4px;">Nenhum estabelecimento registado ainda.</p><p style="font-size: 13px;">Clique em "+ Novo Estabelecimento" para adicionar o primeiro cliente à plataforma.</p></div></td></tr>';
            }
        }
    }
}

// Função para atualizar os cartões de métricas no topo
function updateMetrics(countChange, revenueChange) {
    var totalEl = document.getElementById('metricTotal');
    var activeCountEl = document.getElementById('metricActiveCount');
    var mrrEl = document.getElementById('metricMRR');

    if (totalEl) {
        var currentTotal = parseInt(totalEl.innerText) || 0;
        totalEl.innerText = Math.max(0, currentTotal + countChange);
    }

    if (activeCountEl) {
        var currentCount = parseInt(activeCountEl.innerText) || 0;
        activeCountEl.innerText = Math.max(0, currentCount + countChange);
    }

    if (mrrEl) {
        var currentText = mrrEl.innerText || 'R$ 0';
        var cleanText = currentText.replace('R$', '').replace(/\./g, '').replace(',', '').trim();
        var currentMRR = parseFloat(cleanText) || 0;
        var newMRR = Math.max(0, currentMRR + revenueChange);
        mrrEl.innerText = 'R$ ' + newMRR.toLocaleString('pt-BR');
    }
}

// Função para processar o formulário de criação de um novo estabelecimento
function handleCreateTenant(event) {
    event.preventDefault();

    var storeNameInput = document.getElementById('storeName');
    var ownerNameInput = document.getElementById('ownerName');
    var ownerEmailInput = document.getElementById('ownerEmail');
    var planSelect = document.getElementById('planSelect');

    if (!storeNameInput || !ownerNameInput || !ownerEmailInput || !planSelect) return;

    var storeName = storeNameInput.value;
    var ownerName = ownerNameInput.value;
    var ownerEmail = ownerEmailInput.value;
    var planValue = planSelect.value;
    
    var planName = "Profissional";
    var planPrice = 199;
    if (planValue === 'basico') {
        planName = "Básico";
        planPrice = 99;
    } else if (planValue === 'enterprise') {
        planName = "Enterprise";
        planPrice = 399;
    }

    var initials = storeName.split(' ').map(function(n) { return n[0]; }).join('').substring(0, 2).toUpperCase();
    if (!initials) initials = "ST";

    var emptyRow = document.getElementById('emptyRow');
    if (emptyRow) {
        emptyRow.remove();
    }

    var tbody = document.getElementById('saasTableBody');
    if (!tbody) return;

    var newRow = document.createElement('tr');

    newRow.innerHTML = '<td>' +
        '<div class="tenant-cell-info">' +
            '<div class="tenant-avatar">' + initials + '</div>' +
            '<div>' +
                '<div class="tenant-name">' + storeName + '</div>' +
                '<div class="tenant-sub">' + ownerName + ' (' + ownerEmail + ')</div>' +
            '</div>' +
        '</div>' +
    '</td>' +
    '<td>' +
        '<strong>' + planName + '</strong><br>' +
        '<span style="font-size: 12px; color: var(--gray);">R$ ' + planPrice + ',00 / mês</span>' +
    '</td>' +
    '<td>21/10/2026</td>' +
    '<td><span class="badge-saas active">● Ativo</span></td>' +
    '<td style="text-align: right;">' +
        '<div class="action-btns-group" style="justify-content: flex-end;">' +
            '<button class="btn-table-action" onclick="viewTenant()">Gerir</button>' +
            '<button class="btn-table-action danger" onclick="removeTenant(this, ' + planPrice + ')">Remover</button>' +
        '</div>' +
    '</td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    updateMetrics(1, planPrice);
    alert('Sucesso! A conta do estabelecimento "' + storeName + '" foi criada com sucesso.');
    closeModal();
}

// Filtro por abas (Todos, Ativos, Pendentes)
function setFilter(type, buttonElement) {
    var tabs = document.querySelectorAll('.filter-tab');
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
    
    var rows = document.querySelectorAll('#saasTableBody tr:not(#emptyRow)');
    for (var j = 0; j < rows.length; j++) {
        var row = rows[j];
        var isPending = row.innerHTML.indexOf('Pendente') !== -1;
        if (type === 'all') {
            row.style.display = '';
        } else if (type === 'ativo' && isPending) {
            row.style.display = 'none';
        } else if (type === 'pendente' && !isPending) {
            row.style.display = 'none';
        } else {
            row.style.display = '';
        }
    }
}

// Pesquisa dinâmica de inquilinos
function filterTenants() {
    var searchInput = document.getElementById("searchTenant");
    if (!searchInput) return;
    var query = searchInput.value.toLowerCase();
    var rows = document.querySelectorAll('#saasTableBody tr:not(#emptyRow)');
    
    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var text = row.innerText.toLowerCase();
        if (text.indexOf(query) !== -1) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

function exportSaasReport() {
    alert('A gerar relatório executivo de assinaturas da plataforma...');
}

function handleLogout() {
    window.location.href = "index.html";
}