
function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.querySelectorAll('.btn-delete-security').forEach(button => {
    button.addEventListener('click', function () {
        const id = this.dataset.id;

        if (confirm('Are you sure you want to delete this security?')) {
            fetch(`/api/security/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
                .then(res => {
                    if (res.ok) {
                        location.reload(); // hoặc bạn có thể remove row DOM nếu thích
                    } else {
                        alert('Failed to delete transaction.');
                    }
                })
                .catch(() => alert('Request failed.'));
        }
    });
});

const btn = document.getElementById('btn-add-security').addEventListener('click', () => {
    fetch('/security/search/')
        .then(res => res.text())
        .then(html => {
            document.getElementById('modal-container').innerHTML = html;
            const modalEl = document.getElementById('tickerSearchModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        })
        .catch(err => console.error('Could not load security search modal:', err));
});

document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'btn-add_security') {
        const btn = e.target;
        const row = btn.closest('tr');
        if (!row) return;

        const tds = row.querySelectorAll('td');
        const code = tds[1]?.textContent.trim() || '';
        const exchange = tds[2]?.textContent.trim() || '';
        const name = tds[3]?.textContent.trim() || '';
        const type = tds[4]?.textContent.trim() || '';
        const currency = tds[5]?.textContent.trim() || '';
        const country = tds[6]?.textContent.trim() || '';
        const api_source = btn.dataset.api || 'unknown';

        const data = {
            code,
            exchange,
            name,
            type,
            currency,
            country,
            api_source,
        };

        fetch('/api/security/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(data),
        })
        .then(res => res.json())
        .then(res => {
            alert(res.status === 'ok' ? 'Added!' : 'Already exists.');
        })
        .catch(() => {
            alert('Error adding security');
        });
    } else if (e.target.id === 'close-search-btn') {
        location.reload();
    }
});

document.addEventListener('keydown', function (e) {
    // Check đúng input id và phím Enter
    if (e.target && e.target.id === 'search-ticker' && (e.key === 'Enter' || e.keyCode === 13)) {
        e.preventDefault();
        const query = e.target.value.trim();
        const tbody = document.getElementById('securities-table-body');

        if (query.length < 2) {
            tbody.innerHTML = '';
            return;
        }

        // Build query param string
        const params = new URLSearchParams({ q: query });

        fetch(`/api/security/search/?${params.toString()}`)
            .then(res => {
                if (!res.ok) throw new Error('Network response not ok');
                return res.json();
            })
            .then(data => {
                tbody.innerHTML = '';

                const yahoo = data.yahoo || [];
                const eodhd = data.eodhd || [];

                if (Array.isArray(yahoo)) {
                    yahoo.forEach((item, i) => {
                        const code = item.symbol || '';
                        const exchange = item.exchange || '';
                        const name = item.shortname || item.longname || '';
                        const type = item.quoteType || '';
                        const currency = item.currency || '';
                        const country = item.country || '';

                        tbody.insertAdjacentHTML('beforeend', `
                <tr>
                    <td>${i + 1}</td>
                    <td>${code}</td>
                    <td>${exchange}</td>
                    <td>${name}</td>
                    <td>${type}</td>
                    <td>${currency}</td>
                    <td>${country}</td>
                    <td>yahoo</td>
                    <td><button class="btn btn-sm btn-link" id="btn-add_security" data-api="yahoo">Add</button></td>
                </tr>
                `);
                    });
                }

                if (Array.isArray(eodhd)) {
                    eodhd.forEach((item, j) => {
                        const code = item.Code || '';
                        const exchange = item.Exchange || '';
                        const name = item.Name || '';
                        const type = item.Type || '';
                        const currency = item.Currency || '';
                        const country = item.Country || '';

                        tbody.insertAdjacentHTML('beforeend', `
                <tr>
                    <td>${yahoo.length + j + 1}</td>
                    <td>${code}</td>
                    <td>${exchange}</td>
                    <td>${name}</td>
                    <td>${type}</td>
                    <td>${currency}</td>
                    <td>${country}</td>
                    <td>eodhd</td>
                    <td><button class="btn btn-sm btn-link" id="btn-add_security" data-api="eodhd">Add</button></td>
                </tr>
                `);
                    });
                }

                if (!yahoo.length && !eodhd.length) {
                    tbody.innerHTML = '<tr><td colspan="8" class="text-center">No results found</td></tr>';
                }
            })
            .catch(() => {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading data</td></tr>';
            });
    }
});
