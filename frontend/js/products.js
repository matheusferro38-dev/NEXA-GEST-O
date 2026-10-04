// Lógica do Módulo de Produtos / Stock - Nexa Gestão

document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
});

function openProductModal() {
    var modal = document.getElementById('productModal');
    if (modal) modal.classList.add('open');
}

function closeProductModal() {
    var modal = document.getElementById('productModal');
    var form = document.getElementById('newProductForm');
    if (modal) modal.classList.remove('open');
    if (form) form.reset();
}

function loadProducts() {
    updateProductMetrics();
}

function handleCreateProduct(event) {
    event.preventDefault();

    var nameInput = document.getElementById('prodNameInput');
    var catInput = document.getElementById('prodCategoryInput');
    var priceInput = document.getElementById('prodPriceInput');
    var qtyInput = document.getElementById('prodQtyInput');

    if (!nameInput || !catInput || !priceInput || !qtyInput) return;

    var name = nameInput.value.trim();
    var category = catInput.value.trim();
    var price = parseFloat(priceInput.value) || 0;
    var quantity = parseInt(qtyInput.value) || 0;

    if (!name || price <= 0 || quantity < 0) return;

    var tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    var emptyState = tbody.querySelector('.empty-row-state');
    if (emptyState) {
        tbody.innerHTML = '';
    }

    var newRow = document.createElement('tr');
    var formattedPrice = 'R$ ' + price.toFixed(2).replace('.', ',');

    newRow.innerHTML = '<td><strong>' + name + '</strong></td>' +
        '<td>' + category + '</td>' +
        '<td>' + formattedPrice + '</td>' +
        '<td>' + quantity + ' unidades</td>' +
        '<td style="text-align: right;"><button class="btn-delete-product" onclick="deleteProduct(this)">Excluir</button></td>';

    tbody.insertBefore(newRow, tbody.firstChild);

    updateProductMetrics();
    closeProductModal();
}

function deleteProduct(buttonElement) {
    if (confirm('Tem certeza de que deseja excluir este produto do stock?')) {
        var row = buttonElement.closest('tr');
        if (row) {
            row.remove();
        }

        var tbody = document.getElementById('productsTableBody');
        if (tbody && tbody.querySelectorAll('tr').length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-row-state">Nenhum produto registado no stock.</td></tr>';
        }

        updateProductMetrics();
    }
}

function updateProductMetrics() {
    var tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    var rows = tbody.querySelectorAll('tr');
    var hasEmpty = tbody.querySelector('.empty-row-state');

    var totalProducts = 0;
    var totalUnits = 0;
    var categoriesSet = {};

    if (!hasEmpty) {
        totalProducts = rows.length;

        for (var i = 0; i < rows.length; i++) {
            var catCell = rows[i].querySelector('td:nth-child(2)');
            var qtyCell = rows[i].querySelector('td:nth-child(4)');

            if (catCell) {
                var catText = catCell.innerText.trim();
                categoriesSet[catText] = true;
            }

            if (qtyCell) {
                var qtyNum = parseInt(qtyCell.innerText) || 0;
                totalUnits += qtyNum;
            }
        }
    }

    var categoriesCount = Object.keys(categoriesSet).length;

    var prodEl = document.getElementById('metricTotalProducts');
    var unitsEl = document.getElementById('metricTotalUnits');
    var catEl = document.getElementById('metricCategoriesCount');

    if (prodEl) prodEl.innerText = totalProducts;
    if (unitsEl) unitsEl.innerText = totalUnits;
    if (catEl) catEl.innerText = categoriesCount;
}

function exportProductReport() {
    var tbody = document.getElementById('productsTableBody');
    var rows = tbody ? tbody.querySelectorAll('tr') : [];
    
    if (rows.length === 0 || tbody.querySelector('.empty-row-state')) {
        alert('Não existem produtos registados no stock para exportar.');
        return;
    }

    alert('Relatório de stock exportado com sucesso!');
}