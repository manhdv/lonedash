
document.addEventListener('click', function (e) {
    if (e.target) {
        if (e.target.id === 'btn-add-entry') {
            fetch(`/trade/create/`)
                .then(response => response.text())
                .then(data => {
                    document.getElementById('modal-container').innerHTML = data;
                    const modalEl = document.getElementById('addTradeModal');
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                })
                .catch(error => {
                    console.error('Error loading trade form:', error);
                });
        }
    }
});


document.querySelectorAll('.btn-delete-entry').forEach(button => {
    button.addEventListener('click', function () {
        const id = this.dataset.id;

        if (confirm('Are you sure you want to delete this entry?')) {
            fetch(`/api/entry/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
                .then(res => {
                    if (res.ok) {
                        location.reload(); // hoặc bạn có thể remove row DOM nếu thích
                    } else {
                        showError('Failed to delete entry.');
                    }
                })
                .catch(() => showError('Request failed.'));
        }
    });
});

document.addEventListener('submit', function (e) {
    if (e.target && e.target.id === 'trade-form') {
        e.preventDefault();

        const form = e.target;
        const url = form.action;

        const formData = new FormData(form);
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        const method = url.match(/\/\d+\/?$/) ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(jsonData)
        })
            .then(res => {
                if (res.ok) return res.json();
                return res.json().then(data => Promise.reject(data));
            })
            .then(data => {
                const modalEl = document.getElementById('addTradeModal');
                if (modalEl) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }
                location.reload();
            })
            .catch(data => {
                if (data.errors) {
                    for (let field in data.errors) {
                        const input = document.getElementById(`id_trade_${field}`);
                        if (input) {
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'field-error text-danger small mt-1';
                            errorDiv.innerText = data.errors[field].join(', ');
                            input.parentNode.insertBefore(errorDiv, input.nextSibling);
                        }
                    }
                } else {
                    alert('Error updating trade');
                }
            });
    }
});

document.addEventListener('input', function (e) {
    if (
        e.target &&
        ['id_trade_quantity', 'id_trade_price', 'id_trade_fee', 'id_trade_tax'].includes(e.target.id)
    ) {
        const modal = document.getElementById('addTradeModal');
        if (!modal) return;

        const quantityInput = modal.querySelector('#id_trade_quantity');
        const priceInput = modal.querySelector('#id_trade_price');
        const feeInput = modal.querySelector('#id_trade_fee');
        const taxInput = modal.querySelector('#id_trade_tax');
        const grossAmountInput = modal.querySelector('#id_trade_gross_amount');
        const netAmountInput = modal.querySelector('#id_trade_net_amount');

        if (!quantityInput || !priceInput || !feeInput || !taxInput || !grossAmountInput || !netAmountInput) return;

        const quantity = parseFloat(quantityInput.value) || 0;
        const price = parseFloat(priceInput.value) || 0;
        const fee = parseFloat(feeInput.value) || 0;
        const tax = parseFloat(taxInput.value) || 0;

        const gross = quantity * price;
        const net = gross - fee - tax;

        grossAmountInput.value = gross.toFixed(2);
        netAmountInput.value = net.toFixed(2);
    }
});
