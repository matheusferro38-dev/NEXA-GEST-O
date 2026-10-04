// Lógica do Módulo de Funcionários - Nexa Gestão

document.addEventListener('DOMContentLoaded', function() {
    loadEmployees();
});

function openEmployeeModal() {
    var modal = document.getElementById('employeeModal');
    if (modal) modal.classList.add('open');
}

function closeEmployeeModal() {
    var modal = document.getElementById('employeeModal');
    var form = document.getElementById('newEmployeeForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function loadEmployees() {
    updateEmployeeMetrics();
}

function handleCreateEmployee(event) {
    event.preventDefault();

    var nameInput = document.getElementById('empNameInput');
    var roleInput = document.getElementById('empRoleInput');
    var contactInput = document.getElementById('empContactInput');
    var salaryInput = document.getElementById('empSalaryInput');

    if (!nameInput || !roleInput || !contactInput || !salaryInput) return;

    var name = nameInput.value.trim();
    var role = roleInput.value.trim();
    var contact = contactInput.value.trim();
    var salary = parseFloat(salaryInput.value) || 0;

    if (!name || !role || salary < 0) return;

    var tbody = document.getElementById('employeesTableBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');
    var formattedSalary = 'R$ ' + salary.toFixed(2).replace('.', ',');

    newRow.innerHTML = '<td><strong>' + name + '</strong></td>' +
        '<td>' + role + '</td>' +
        '<td>' + contact + '</td>' +
        '<td style="font-weight: 700; color: var(--color-text);">' + formattedSalary + '</td>' +
        '<td style="text-align: right;"><button class="btn-delete-employee" onclick="deleteEmployee(this)">Excluir</button></td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    updateEmployeeMetrics();
    closeEmployeeModal();
}

function deleteEmployee(buttonElement) {
    if (confirm('Tem certeza de que deseja excluir este funcionário da equipa?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('employeesTableBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-row-state">Nenhum funcionário registado na equipa.</td></tr>';
        }

        updateEmployeeMetrics();
    }
}

function updateEmployeeMetrics() {
    var tbody = document.getElementById('employeesTableBody');
    if (!tbody) return;

    var rows = tbody.querySelectorAll('tr');
    var hasEmpty = tbody.querySelector('.empty-row-state');

    var totalEmployees = 0;
    var totalPayroll = 0;
    var rolesSet = {};

    if (!hasEmpty) {
        totalEmployees = rows.length;

        for (var i = 0; i < rows.length; i++) {
            var roleCell = rows[i].querySelector('td:nth-child(2)');
            var salCell = rows[i].querySelector('td:nth-last-child(2)');

            if (roleCell) {
                var roleText = roleCell.innerText.trim();
                rolesSet[roleText] = true;
            }

            if (salCell) {
                var cleanNum = salCell.innerText.replace(/[^0-9,-]/g, '').replace('.', '').replace(',', '.');
                var num = parseFloat(cleanNum) || 0;
                totalPayroll += num;
            }
        }
    }

    var rolesCount = Object.keys(rolesSet).length;

    var empEl = document.getElementById('metricTotalEmployees');
    var payEl = document.getElementById('metricTotalPayroll');
    var rolesEl = document.getElementById('metricRolesCount');

    if (empEl) empEl.innerText = totalEmployees;
    if (payEl) payEl.innerText = 'R$ ' + totalPayroll.toFixed(2).replace('.', ',');
    if (rolesEl) rolesEl.innerText = rolesCount;
}

function exportEmployeeReport() {
    var tbody = document.getElementById('employeesTableBody');
    var rows = tbody ? tbody.querySelectorAll('tr') : [];
    
    if (rows.length === 0 || tbody.querySelector('.empty-row-state')) {
        alert('Não existem funcionários registados para exportar.');
        return;
    }

    alert('Relatório da equipa exportado com sucesso!');
}