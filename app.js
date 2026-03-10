const state = {
  selectedCategoryId: '',
  selectedItemId: '',
  queue: []
};

const els = {
  categorySelect: document.getElementById('categorySelect'),
  itemSelect: document.getElementById('itemSelect'),
  qtyInput: document.getElementById('qtyInput'),
  addBtn: document.getElementById('addBtn'),
  queueList: document.getElementById('queueList'),
  summaryList: document.getElementById('summaryList'),
  itemsCountBadge: document.getElementById('itemsCountBadge'),
  resourcesCountBadge: document.getElementById('resourcesCountBadge'),
  categoryPills: document.getElementById('categoryPills'),
  selectedPreview: document.getElementById('selectedPreview')
};

function getCategories() {
  return window.CRAFT_DATA.categories;
}

function getSelectedCategory() {
  return getCategories().find(c => c.id === state.selectedCategoryId) || null;
}

function getSelectedItem() {
  const category = getSelectedCategory();
  if (!category) return null;
  return category.items.find(i => i.id === state.selectedItemId) || null;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function initialsFromName(name) {
  const words = String(name).trim().split(/\s+/).slice(0, 2);
  return words.map(word => word[0]?.toUpperCase() || '').join('').slice(0, 3) || '?';
}

function renderThumb(item, { large = false } = {}) {
  const extra = large ? ' large' : '';
  if (item?.image) {
    return `<div class="item-thumb${extra}"><img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}" loading="lazy"></div>`;
  }

  const label = item?.thumbLabel || initialsFromName(item?.name || '?');
  return `<div class="item-thumb placeholder${extra}">${escapeHtml(label)}</div>`;
}

function renderCategoryOptions() {
  const categories = getCategories();
  els.categorySelect.innerHTML = categories
    .map(cat => `<option value="${cat.id}">${cat.icon} ${escapeHtml(cat.name)}</option>`)
    .join('');

  if (!state.selectedCategoryId && categories.length) {
    state.selectedCategoryId = categories[0].id;
  }

  els.categorySelect.value = state.selectedCategoryId;
}

function renderItemOptions() {
  const category = getSelectedCategory();
  const items = category?.items || [];

  if (!items.length) {
    state.selectedItemId = '';
    els.itemSelect.innerHTML = '<option value="">В этой категории пока нет предметов</option>';
    els.itemSelect.value = '';
    els.itemSelect.disabled = true;
    els.addBtn.disabled = true;
    renderSelectedPreview();
    return;
  }

  if (!items.some(item => item.id === state.selectedItemId)) {
    state.selectedItemId = items[0].id;
  }

  els.itemSelect.disabled = false;
  els.itemSelect.innerHTML = items
    .map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`)
    .join('');
  els.itemSelect.value = state.selectedItemId;
  els.addBtn.disabled = false;
  renderSelectedPreview();
}

function renderCategoryPills() {
  els.categoryPills.innerHTML = getCategories()
    .map(cat => {
      const isEmpty = cat.items.length === 0;
      return `
        <div class="category-pill ${isEmpty ? 'empty' : ''}">
          <span>${cat.icon}</span>
          <span>${escapeHtml(cat.name)}</span>
          <span>${isEmpty ? '0' : cat.items.length}</span>
        </div>
      `;
    })
    .join('');
}

function renderSelectedPreview() {
  const category = getSelectedCategory();
  const item = getSelectedItem();

  if (!category || !item) {
    els.selectedPreview.innerHTML = `
      <div class="selected-thumb item-thumb large placeholder">?</div>
      <div>
        <div class="selected-title">Выбери предмет</div>
        <div class="selected-subtitle">Категория и рецепт появятся здесь</div>
      </div>
    `;
    return;
  }

  els.selectedPreview.innerHTML = `
    ${renderThumb(item, { large: true })}
    <div>
      <div class="selected-title">${escapeHtml(item.name)}</div>
      <div class="selected-subtitle">${escapeHtml(category.name)} · ${item.recipe.length} ${pluralize(item.recipe.length, ['компонент', 'компонента', 'компонентов'])}</div>
    </div>
  `;
}

function addCurrentItem() {
  const item = getSelectedItem();
  const category = getSelectedCategory();
  const qty = Math.max(1, Number(els.qtyInput.value) || 1);

  if (!item || !category) return;

  state.queue.push({
    entryId: crypto.randomUUID(),
    categoryId: category.id,
    categoryName: category.name,
    categoryIcon: category.icon,
    itemId: item.id,
    itemName: item.name,
    itemImage: item.image || '',
    thumbLabel: item.thumbLabel || initialsFromName(item.name),
    qty,
    recipe: item.recipe
  });

  renderAll();
}

function removeQueueItem(entryId) {
  state.queue = state.queue.filter(item => item.entryId !== entryId);
  renderAll();
}

function getSummary() {
  const totals = new Map();

  for (const entry of state.queue) {
    for (const ingredient of entry.recipe) {
      const existing = totals.get(ingredient.name) || {
        name: ingredient.name,
        qty: 0,
        image: ingredient.image || '',
        thumbLabel: ingredient.thumbLabel || initialsFromName(ingredient.name)
      };

      existing.qty += ingredient.qty * entry.qty;
      if (!existing.image && ingredient.image) {
        existing.image = ingredient.image;
      }
      totals.set(ingredient.name, existing);
    }
  }

  return [...totals.values()].sort((a, b) => b.qty - a.qty || a.name.localeCompare(b.name, 'ru'));
}

function renderQueue() {
  els.itemsCountBadge.textContent = `${state.queue.length} ${pluralize(state.queue.length, ['позиция', 'позиции', 'позиций'])}`;

  if (!state.queue.length) {
    els.queueList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">☢</div>
        <div class="empty-title">Список пока пуст</div>
        <div class="empty-text">Добавь предмет слева — и калькулятор сразу соберёт итоговые ресурсы.</div>
      </div>
    `;
    return;
  }

  els.queueList.innerHTML = state.queue
    .map(entry => `
      <div class="queue-item">
        ${renderThumb({ name: entry.itemName, image: entry.itemImage, thumbLabel: entry.thumbLabel })}
        <div class="queue-main">
          <div class="queue-title">${escapeHtml(entry.itemName)}</div>
          <div class="queue-meta">${escapeHtml(entry.categoryIcon)} ${escapeHtml(entry.categoryName)}</div>
        </div>
        <div class="qty-chip">x${entry.qty}</div>
        <button class="remove-btn" type="button" data-remove-id="${entry.entryId}">Убрать</button>
      </div>
    `)
    .join('');

  els.queueList.querySelectorAll('[data-remove-id]').forEach(btn => {
    btn.addEventListener('click', () => removeQueueItem(btn.dataset.removeId));
  });
}

function renderSummary() {
  const summary = getSummary();
  els.resourcesCountBadge.textContent = `${summary.length} ${pluralize(summary.length, ['ресурс', 'ресурса', 'ресурсов'])}`;

  if (!summary.length) {
    els.summaryList.innerHTML = `
      <div class="empty-state compact">
        <div class="empty-title">Пока нечего считать</div>
        <div class="empty-text">Выбери предмет и добавь его в список.</div>
      </div>
    `;
    return;
  }

  els.summaryList.innerHTML = summary
    .map(item => `
      <div class="summary-item">
        ${renderThumb(item)}
        <div class="summary-main">
          <div class="summary-title">${escapeHtml(item.name)}</div>
          <div class="summary-meta">Суммарная потребность</div>
        </div>
        <div class="total-chip">${item.qty}</div>
      </div>
    `)
    .join('');
}

function pluralize(value, forms) {
  const abs = Math.abs(value) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return forms[2];
  if (last > 1 && last < 5) return forms[1];
  if (last === 1) return forms[0];
  return forms[2];
}

function renderAll() {
  renderCategoryOptions();
  renderItemOptions();
  renderCategoryPills();
  renderQueue();
  renderSummary();
  renderSelectedPreview();
}

function wireEvents() {
  els.categorySelect.addEventListener('change', () => {
    state.selectedCategoryId = els.categorySelect.value;
    state.selectedItemId = '';
    renderItemOptions();
  });

  els.itemSelect.addEventListener('change', () => {
    state.selectedItemId = els.itemSelect.value;
    renderSelectedPreview();
  });

  els.addBtn.addEventListener('click', addCurrentItem);

  els.qtyInput.addEventListener('input', () => {
    const value = Number(els.qtyInput.value);
    if (!Number.isFinite(value) || value < 1) {
      els.qtyInput.value = 1;
    }
  });
}

function init() {
  const firstCategory = getCategories()[0];
  state.selectedCategoryId = firstCategory?.id || '';
  state.selectedItemId = firstCategory?.items?.[0]?.id || '';
  wireEvents();
  renderAll();
}

init();
