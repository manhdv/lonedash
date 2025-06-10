function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function showError(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dismissible alert-danger fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}

function showWarning(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dissmissible alert-warning fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}


function showSuccess(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dissmissible alert-success fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}

function showInfo(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dissmissible alert-info fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}

function showPrimary(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dissmissible alert-primary fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}


function showSecondary(msg) {
    const container = document.getElementById('alerts');
    container.innerHTML = `
      <div class="alert alert-dissmissible alert-secondary fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
}

function showConfirm({ title = 'Confirm', body = 'Are you sure?', onConfirm }) {
  const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
  document.getElementById('confirmModalTitle').textContent = title;
  document.getElementById('confirmModalBody').textContent = body;

  const okBtn = document.getElementById('confirmModalOk');
  const clonedBtn = okBtn.cloneNode(true);  // Clone to remove old listeners
  okBtn.replaceWith(clonedBtn);

  clonedBtn.addEventListener('click', () => {
    modal.hide();
    onConfirm && onConfirm();
  });

  modal.show();
}
