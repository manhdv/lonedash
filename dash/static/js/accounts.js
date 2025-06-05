function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.querySelectorAll('.btn-delete-transaction').forEach(button => {
    button.addEventListener('click', function () {
        const txId = this.dataset.id;

        if (confirm('Are you sure you want to delete this transaction?')) {
            fetch(`/api/transaction/${txId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
                .then(res => {
                    if (res.ok) {
                        location.reload(); // hoặc remove row khỏi DOM nếu muốn fancy
                    } else {
                        alert('Failed to delete transaction.');
                    }
                })
                .catch(() => alert('Request failed.'));
        }
    });
});


document.querySelectorAll('.btn-edit-transaction').forEach(button => {
    button.addEventListener('click', function () {
        const txId = this.dataset.id;

        fetch(`/transaction/edit/${txId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load form');
                return res.text();
            })
            .then(html => {
                document.getElementById('modal-container').innerHTML = html;
                const modalEl = document.getElementById('addTransactionModal');
                new bootstrap.Modal(modalEl).show();
            })
            .catch(err => {
                alert('Could not load transaction form.');
                console.error(err);
            });

    });
});


document.getElementById('btn-add-transaction').addEventListener('click', () => {
    fetch('/transaction/create/')
        .then(res => res.text())
        .then(data => {
            document.getElementById('modal-container').innerHTML = data;
            const modalEl = document.getElementById('addTransactionModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        })
        .catch(err => console.error('Error loading transaction form:', err));
});

document.addEventListener('submit', function (e) {
    if (e.target && e.target.id === 'transaction-form') {
        e.preventDefault();

        const form = e.target;
        const url = form.action;

        const formData = new FormData(form);
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        const method = /\/\d+\/?$/.test(url) ? 'PUT' : 'POST';

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
                const modalEl = document.getElementById('addTransactionModal');
                if (modalEl) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }
                location.reload();
            })
            .catch(data => {
                if (data.errors) {
                    Object.keys(data.errors).forEach(field => {
                        const input = document.getElementById(`id_transaction_${field}`);
                        if (input) {
                            // Remove old error if any
                            const oldError = input.nextElementSibling;
                            if (oldError && oldError.classList.contains('field-error')) {
                                oldError.remove();
                            }
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'field-error text-danger small mt-1';
                            errorDiv.textContent = data.errors[field].join(', ');
                            input.insertAdjacentElement('afterend', errorDiv);
                        }
                    });
                } else {
                    alert('Error updating transaction');
                }
            });
    }
});


document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-delete_account')) {
        const accId = e.target.dataset.id;

        if (confirm('Are you sure you want to delete this account?')) {
            fetch(`/api/account/${accId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
                .then(res => {
                    if (res.ok) {
                        location.reload(); // hoặc tự remove row nếu thích sống ảo
                    } else {
                        alert('Failed to delete account.');
                    }
                })
                .catch(() => alert('Request failed.'));
        }
    }
});
document.getElementById('btn-add-account').addEventListener('click', () => {
    fetch('/account/create')
        .then(res => res.text())
        .then(data => {
            document.getElementById('modal-container').innerHTML = data;
            const modalEl = document.getElementById('addAccountModal');
            new bootstrap.Modal(modalEl).show();
        })
        .catch(err => console.error('Error loading account form:', err));
});


document.querySelectorAll('.btn-edit_account').forEach(button => {
    button.addEventListener('click', function () {
        const accId = e.target.dataset.id;
        fetch(`/account/edit/${accId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load form');
                return res.text();
            })
            .then(html => {
                document.getElementById('modal-container').innerHTML = html;
                const modalEl = document.getElementById('addAccountModal');
                new bootstrap.Modal(modalEl).show();
            })
            .catch(err => {
                alert('Could not load account form.');
                console.error(err);
            });
    });
});

// delegate submit because #account-form is injected dynamically
document.addEventListener('submit', (e) => {
    if (e.target.id === 'account-form') {
        e.preventDefault();

        const form = e.target;
        const url = form.action;

        // build plain-object payload
        const jsonData = {};
        new FormData(form).forEach((v, k) => (jsonData[k] = v));

        // choose POST vs PUT by url pattern
        const method = /\/\d+\/?$/.test(url) ? 'PUT' : 'POST';

        fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(jsonData)
        })
            .then(res => {
                if (res.ok) return res.json();
                return res.json().then(err => Promise.reject(err));
            })
            .then(() => {
                // hide Bootstrap modal without jQuery
                const modalEl = document.getElementById('addAccountModal');
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();
                location.reload();
            })
            .catch(data => {
                // clear old errors
                form.querySelectorAll('.field-error').forEach(el => el.remove());

                if (data.errors) {
                    for (const field in data.errors) {
                        const input = document.getElementById(`id_account_${field}`);
                        if (!input) continue;
                        const errDiv = document.createElement('div');
                        errDiv.className = 'field-error text-danger small mt-1';
                        errDiv.textContent = data.errors[field].join(', ');
                        input.insertAdjacentElement('afterend', errDiv);
                    }
                } else {
                    alert('Error updating account');
                }
            });
    }
});

