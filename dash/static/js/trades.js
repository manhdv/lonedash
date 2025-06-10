
document.addEventListener('click', function (e) {
    if (e.target) {
        if (e.target.id === 'btn-add-entry') {
            fetch(`/entry/create/`)
                .then(response => response.text())
                .then(data => {
                    document.getElementById('modal-container').innerHTML = data;
                    const modalEl = document.getElementById('addEntryModal');
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

document.querySelectorAll('.btn-edit_entry').forEach(button => {
    button.addEventListener('click', function (e) {
        const id = e.target.dataset.id;
        fetch(`/entry/edit/${id}/`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load form');
                return res.text();
            })
            .then(html => {
                document.getElementById('modal-container').innerHTML = html;
                const modalEl = document.getElementById('addEntryModal');
                new bootstrap.Modal(modalEl).show();
                recalcEntryAmounts();
            })
            .catch(err => {
                showError('Could not load entry form.');
                console.error(err);
            });
    });
});

document.addEventListener('submit', function (e) {
    if (e.target && e.target.id === 'entry-form') {
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
                const modalEl = document.getElementById('addEntryModal');
                if (modalEl) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }
                location.reload();
            })
            .catch(data => {
                // Clear cũ
                form.querySelectorAll('.field-error').forEach(el => el.remove());

                if (data.errors) {
                    for (let field in data.errors) {
                        const input = document.getElementById(`id_entry_${field}`);
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


document.addEventListener('click', function (e) {
    if (e.target) {
        if (e.target.id === 'btn-add-exit') {
            fetch(`/exit/create/`)
                .then(response => response.text())
                .then(data => {
                    document.getElementById('modal-container').innerHTML = data;
                    const modalEl = document.getElementById('addExitModal');
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                })
                .catch(error => {
                    console.error('Error loading trade form:', error);
                });
        }
    }
});


document.querySelectorAll('.btn-delete-exit').forEach(button => {
    button.addEventListener('click', function () {
        const id = this.dataset.id;

        if (confirm('Are you sure you want to delete this exit?')) {
            fetch(`/api/exit/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
                .then(res => {
                    if (res.ok) {
                        location.reload(); // hoặc bạn có thể remove row DOM nếu thích
                    } else {
                        showError('Failed to delete exit.');
                    }
                })
                .catch(() => showError('Request failed.'));
        }
    });
});

document.querySelectorAll('.btn-edit_exit').forEach(button => {
    button.addEventListener('click', function (e) {
        const id = e.target.dataset.id;
        fetch(`/exit/edit/${id}/`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load form');
                return res.text();
            })
            .then(html => {
                document.getElementById('modal-container').innerHTML = html;
                const modalEl = document.getElementById('addExitModal');
                new bootstrap.Modal(modalEl).show();
                recalcExitAmounts();
            })
            .catch(err => {
                showError('Could not load entry form.');
                console.error(err);
            });
    });
});

document.addEventListener('submit', function (e) {
    if (e.target && e.target.id === 'exit-form') {
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
                const modalEl = document.getElementById('addExitModal');
                if (modalEl) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }
                location.reload();
            })
            .catch(data => {

                form.querySelectorAll('.field-error').forEach(el => el.remove());

                if (data.errors) {
                    for (let field in data.errors) {
                        const input = document.getElementById(`id_exit_${field}`);
                        if (input) {
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'field-error text-danger small mt-1';
                            errorDiv.innerText = data.errors[field].join(', ');
                            input.parentNode.insertBefore(errorDiv, input.nextSibling);
                        }
                    }
                } else {
                    alert('Error updating exit');
                }
            });
    }
});


function recalcEntryAmounts() {
    const modal = document.getElementById('addEntryModal');
    if (!modal) return;

    const quantityInput = modal.querySelector('#id_entry_quantity');
    const priceInput = modal.querySelector('#id_entry_price');
    const feeInput = modal.querySelector('#id_entry_fee');
    const taxInput = modal.querySelector('#id_entry_tax');
    const grossAmountInput = modal.querySelector('#id_entry_gross_amount');
    const netAmountInput = modal.querySelector('#id_entry_net_amount');

    if (!quantityInput || !priceInput || !feeInput || !taxInput || !grossAmountInput || !netAmountInput) return;

    const quantity = parseFloat(quantityInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const fee = parseFloat(feeInput.value) || 0;
    const tax = parseFloat(taxInput.value) || 0;

    const gross = quantity * price;
    const net = gross + fee + tax;

    grossAmountInput.value = gross.toFixed(2);
    netAmountInput.value = net.toFixed(2);
}



document.addEventListener('input', function (e) {
    if (
        e.target &&
        ['id_entry_quantity', 'id_entry_price', 'id_entry_fee', 'id_entry_tax'].includes(e.target.id)
    ) {
        recalcEntryAmounts();
    }
});



function recalcExitAmounts() {
    const modal = document.getElementById('addExitModal');
    if (!modal) return;

    const quantityInput = modal.querySelector('#id_exit_quantity');
    const priceInput = modal.querySelector('#id_exit_price');
    const feeInput = modal.querySelector('#id_exit_fee');
    const taxInput = modal.querySelector('#id_exit_tax');
    const grossAmountInput = modal.querySelector('#id_exit_gross_amount');
    const netAmountInput = modal.querySelector('#id_exit_net_amount');

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
document.addEventListener('input', function (e) {
    if (
        e.target &&
        ['id_exit_quantity', 'id_exit_price', 'id_exit_fee', 'id_exit_tax'].includes(e.target.id)
    ) {
        recalcExitAmounts();
    }
});

