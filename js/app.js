function toggleHeader() {
  var header = document.getElementById("full-header");
  var btn = document.querySelector(".menu-toggle");
  if (!header || !btn) return;
  header.classList.toggle("expanded");
  btn.setAttribute("aria-expanded", header.classList.contains("expanded") ? "true" : "false");
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function bootCatalog() {
  window.GZ = window.GZ || {};
  GZ.ITEMS = {};
  GZ.CRAFTABLE = [];
  GZ.PRICES = [];
  GZ.STATUS = Object.assign({}, GZ.SEED_STATUS || {});
  GZ.CRAFT_CATEGORIES = {};

  var generated = window.GZ_GENERATED;
  var fromServer = generated && generated.status && generated.status.fromServer;

  if (!fromServer) {
    GZ.ITEMS = Object.assign({}, GZ.SEED_ITEMS || {});
    GZ.CRAFTABLE = (GZ.SEED_CRAFTABLE || []).slice();
    GZ.PRICES = (GZ.SEED_PRICES || []).slice();
  }

  if (generated && generated.items && Object.keys(generated.items).length) {
    Object.keys(generated.items).forEach(function (id) {
      GZ.ITEMS[id] = Object.assign({}, GZ.ITEMS[id] || {}, generated.items[id]);
    });
    if (generated.craftable && generated.craftable.length) {
      GZ.CRAFTABLE = generated.craftable.slice();
    }
    if (generated.prices) GZ.PRICES = generated.prices.slice();
    if (generated.status) GZ.STATUS = generated.status;
    if (generated.craftCategories) GZ.CRAFT_CATEGORIES = generated.craftCategories;
  }

  GZ.CRAFTABLE = GZ.CRAFTABLE.filter(function (id) {
    var item = GZ.ITEMS[id];
    return item && item.recipe && item.recipe.length;
  });
  if (fromServer && generated.craftable) {
    GZ.CRAFTABLE = generated.craftable.slice();
  }
}

function itemById(id) {
  return GZ.ITEMS[id] || Object.values(GZ.ITEMS).find(function (item) {
    return item.classname === id || item.name === id;
  });
}

function itemImage(item) {
  if (!item) return "";
  var src = item.image || "";
  var fallback = escapeHtml((item.name || "?").charAt(0));
  if (!src) {
    return '<span class="img-fallback">' + fallback + "</span>";
  }
  return (
    '<img src="' +
    escapeHtml(src) +
    '" alt="' +
    escapeHtml(item.name || "") +
    '" onerror="this.outerHTML=\'<span class=img-fallback>' +
    fallback +
    "</span>'\">"
  );
}

function hasExpandable(item) {
  return Boolean(item && ((item.recipe && item.recipe.length) || (item.tools && item.tools.length)));
}

function whereText(item) {
  if (!item) return "Нет данных.";

  var places = [];
  var seen = {};
  (item.loot || []).forEach(function (zone) {
    var house = zone && zone.house;
    if (!house || seen[house]) return;
    seen[house] = true;
    places.push(house);
  });
  if (places.length) return places.slice(0, 4).join(", ");

  var raw = String(item.where || "").trim();
  if (!raw) return "В файлах сервера пока нет места добычи.";

  var sought = raw.match(/Ищется:\s*([^.]+)\./);
  if (sought) return sought[1].trim();

  return raw
    .replace(/\s*На карте цель экономики[^.]*\.?/g, "")
    .replace(/\s*Зоны:\s*[^.]*\.?/g, "")
    .replace(/^Лут:\s*/i, "")
    .replace(/\s*\([^)]*\)/g, "")
    .replace(/,\s*шанс\s*[^;.]*/gi, "")
    .replace(/;\s*/g, ", ")
    .replace(/\s+/g, " ")
    .replace(/[.,]\s*$/g, "")
    .trim() || "Нет данных.";
}

function initCraftPage() {
  var catalog = document.getElementById("catalog");
  var treeRoot = document.getElementById("tree-root");
  var search = document.getElementById("craft-search");
  var chips = document.getElementById("craft-chips");
  var tooltip = document.getElementById("tooltip");
  if (!catalog || !treeRoot) return;

  if (!GZ.CRAFTABLE.length) {
    catalog.innerHTML = "";
    treeRoot.innerHTML =
      '<div class="empty-state"><h3>Крафт ещё не подключён</h3><p class="muted">Список берётся только из HP_Crafter.json — предметы станка крафта.</p></div>';
    return;
  }

  var currentId = GZ.CRAFTABLE[0];
  var category = "";
  var categoryMap = GZ.CRAFT_CATEGORIES || {};

  function itemCategory(item) {
    if (!item) return "";
    if (item.craftMeta && item.craftMeta.category) return item.craftMeta.category;
    return item.categoryLabel || "";
  }

  function categoryOrder() {
    var keys = Object.keys(categoryMap);
    if (keys.length) return keys;
    var set = {};
    GZ.CRAFTABLE.forEach(function (id) {
      var cat = itemCategory(itemById(id));
      if (cat) set[cat] = true;
    });
    return Object.keys(set).sort(function (a, b) {
      return a.localeCompare(b, "ru");
    });
  }

  function filteredIds() {
    var q = ((search && search.value) || "").trim().toLowerCase();
    return GZ.CRAFTABLE.filter(function (id) {
      var item = itemById(id);
      if (!item) return false;
      if (category) {
        var listed = categoryMap[category];
        if (listed && listed.length) {
          if (listed.indexOf(id) === -1) return false;
        } else if (itemCategory(item) !== category) {
          return false;
        }
      }
      if (!q) return true;
      return (
        item.name.toLowerCase().indexOf(q) !== -1 ||
        String(item.classname || "").toLowerCase().indexOf(q) !== -1
      );
    });
  }

  function showTooltip(item, event) {
    if (!tooltip || !item) return;
    var loot = (item.loot || [])
      .slice(0, 4)
      .map(function (row) {
        return escapeHtml(row.house) + (row.chance ? " · " + escapeHtml(row.chance) : "");
      })
      .join("<br>");
    tooltip.innerHTML =
      "<strong>Где найти</strong><p>" +
      escapeHtml(whereText(item)) +
      (item.qtyNote ? '</p><p class="note">' + escapeHtml(item.qtyNote) : "") +
      "</p>" +
      (loot ? "<p class='note'>" + loot + "</p>" : "");
    tooltip.classList.add("visible");
    moveTooltip(event);
  }

  function hideTooltip() {
    if (tooltip) tooltip.classList.remove("visible");
  }

  function moveTooltip(event) {
    if (!tooltip) return;
    var x = Math.min(event.clientX + 16, window.innerWidth - 340);
    var y = Math.min(event.clientY + 16, window.innerHeight - 160);
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
  }

  function renderNode(part, multiplier) {
    var item = itemById(part.id) || {
      id: part.id,
      name: part.id,
      categoryLabel: "Компонент",
      image: ""
    };
    var qty = (part.qty || 1) * multiplier;
    var expandable = hasExpandable(item);
    var toolMark = item.tool ? '<span class="tool-tag">инструмент</span>' : "";
    var children = [];
    (item.recipe || []).forEach(function (child) {
      children.push(renderNode(child, qty));
    });
    (item.tools || []).forEach(function (child) {
      children.push(renderNode(child, 1));
    });

    return (
      '<div class="tree-node" data-id="' +
      escapeHtml(item.id) +
      '"><div class="tree-row" data-id="' +
      escapeHtml(item.id) +
      '">' +
      (expandable
        ? '<button class="tree-toggle" type="button" aria-label="Раскрыть">+</button>'
        : "") +
      itemImage(item) +
      '<div class="tree-meta"><div class="tree-name">' +
      escapeHtml(item.name) +
      toolMark +
      '</div><div class="tree-sub">' +
      escapeHtml(item.categoryLabel || "—") +
      (expandable ? " · есть крафт" : "") +
      '</div></div><div class="tree-qty">×' +
      escapeHtml(qty) +
      "</div></div>" +
      (expandable ? '<div class="tree-children">' + children.join("") + "</div>" : "") +
      "</div>"
    );
  }

  function renderTree() {
    var item = itemById(currentId);
    if (!item) return;
    var nodes = (item.recipe || [])
      .map(function (part) {
        return renderNode(part, 1);
      })
      .join("");
    treeRoot.innerHTML =
      '<div class="tree-result">' +
      itemImage(item) +
      "<div><h3>" +
      escapeHtml(item.name) +
      "</h3><p class='muted'>" +
      escapeHtml(item.description || whereText(item)) +
      "</p></div></div>" +
      '<p class="tree-hint">Наведите на компонент, чтобы увидеть, где его искать.</p>' +
      (nodes
        ? '<div class="tree-list">' + nodes + "</div>"
        : '<div class="empty-state"><p class="muted">Рецепт для этого предмета ещё не найден в файлах админа.</p></div>');
  }

  function renderChips() {
    if (!chips) return;
    var html =
      '<button type="button" class="chip' +
      (!category ? " active" : "") +
      '" data-cat="">Все</button>';
    categoryOrder().forEach(function (name) {
      var count = (categoryMap[name] || []).length;
      html +=
        '<button type="button" class="chip' +
        (category === name ? " active" : "") +
        '" data-cat="' +
        escapeHtml(name) +
        '">' +
        escapeHtml(name) +
        (count ? " · " + count : "") +
        "</button>";
    });
    chips.innerHTML = html;
  }

  function renderCatalog() {
    var list = filteredIds();
    if (!list.length) {
      catalog.innerHTML =
        '<div class="empty-state"><p class="muted">В этой категории ничего не найдено.</p></div>';
      return;
    }
    if (list.indexOf(currentId) === -1) {
      currentId = list[0];
      renderTree();
    }
    catalog.innerHTML = list
      .map(function (id) {
        var item = itemById(id);
        if (!item) return "";
        return (
          '<button class="catalog-item' +
          (id === currentId ? " active" : "") +
          '" data-id="' +
          escapeHtml(id) +
          '">' +
          itemImage(item) +
          "<div><strong>" +
          escapeHtml(item.name) +
          "</strong><span>" +
          escapeHtml(itemCategory(item) || "—") +
          " · " +
          ((item.recipe && item.recipe.length) || 0) +
          " компонентов</span></div></button>"
        );
      })
      .join("");
  }

  if (chips) {
    chips.addEventListener("click", function (event) {
      var btn = event.target.closest(".chip");
      if (!btn) return;
      category = btn.dataset.cat || "";
      renderChips();
      renderCatalog();
      catalog.scrollTop = 0;
    });
  }

  catalog.addEventListener("click", function (event) {
    var btn = event.target.closest(".catalog-item");
    if (!btn) return;
    currentId = btn.dataset.id;
    renderCatalog();
    renderTree();
  });

  treeRoot.addEventListener("click", function (event) {
    hideTooltip();
    var toggle = event.target.closest(".tree-toggle");
    if (toggle) {
      event.preventDefault();
      var node = toggle.closest(".tree-node");
      node.classList.toggle("open");
      toggle.textContent = node.classList.contains("open") ? "−" : "+";
    }
  });

  treeRoot.addEventListener("mouseover", function (event) {
    var row = event.target.closest(".tree-row");
    if (!row) return;
    showTooltip(itemById(row.dataset.id), event);
  });
  treeRoot.addEventListener("mousemove", function (event) {
    if (event.target.closest(".tree-row")) moveTooltip(event);
  });
  treeRoot.addEventListener("mouseleave", hideTooltip);

  if (search) {
    search.addEventListener("input", function () {
      renderCatalog();
      catalog.scrollTop = 0;
    });
  }

  var hashId = (location.hash || "").replace("#", "");
  if (hashId && itemById(hashId) && GZ.CRAFTABLE.indexOf(itemById(hashId).id) !== -1) {
    currentId = itemById(hashId).id;
    var hashItem = itemById(hashId);
    category = itemCategory(hashItem) || "";
  }

  renderChips();
  renderCatalog();
  renderTree();
}

function initItemsPage() {
  var grid = document.getElementById("items-grid");
  var search = document.getElementById("items-search");
  var chips = document.getElementById("items-chips");
  var more = document.getElementById("items-more");
  if (!grid) return;

  var PAGE = 120;
  var shown = PAGE;
  var category = "";

  function allItems() {
    return Object.keys(GZ.ITEMS)
      .map(function (id) {
        return GZ.ITEMS[id];
      })
      .sort(function (a, b) {
        return (a.name || "").localeCompare(b.name || "", "ru");
      });
  }

  function filtered() {
    var q = ((search && search.value) || "").trim().toLowerCase();
    return allItems().filter(function (item) {
      if (category && item.category !== category && item.categoryLabel !== category) return false;
      if (!q) return true;
      return (
        (item.name || "").toLowerCase().indexOf(q) !== -1 ||
        String(item.classname || "").toLowerCase().indexOf(q) !== -1
      );
    });
  }

  function renderChips() {
    if (!chips) return;
    var set = {};
    allItems().forEach(function (item) {
      if (item.categoryLabel) set[item.category] = item.categoryLabel;
    });
    var html = '<button type="button" class="chip' + (!category ? " active" : "") + '" data-cat="">Все</button>';
    Object.keys(set)
      .sort(function (a, b) {
        return set[a].localeCompare(set[b], "ru");
      })
      .forEach(function (key) {
        html +=
          '<button type="button" class="chip' +
          (category === key ? " active" : "") +
          '" data-cat="' +
          escapeHtml(key) +
          '">' +
          escapeHtml(set[key]) +
          "</button>";
      });
    chips.innerHTML = html;
  }

  function renderGrid() {
    var list = filtered();
    if (!list.length) {
      grid.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1"><h3>Ничего не найдено</h3><p class="muted">Измените поиск или дождитесь файлов админа.</p></div>';
      if (more) more.hidden = true;
      return;
    }
    grid.innerHTML = list
      .slice(0, shown)
      .map(function (item) {
        return (
          '<button class="item-tile" type="button" data-id="' +
          escapeHtml(item.id) +
          '"><span class="badge">' +
          escapeHtml(item.rarity || item.tier || "—") +
          '</span><span class="img-box">' +
          itemImage(item) +
          '</span><span class="label">' +
          escapeHtml(item.name) +
          "</span></button>"
        );
      })
      .join("");
    if (more) more.hidden = list.length <= shown;
  }

  grid.addEventListener("click", function (event) {
    var tile = event.target.closest(".item-tile");
    if (tile) openItemModal(tile.dataset.id);
  });
  if (chips) {
    chips.addEventListener("click", function (event) {
      var btn = event.target.closest(".chip");
      if (!btn) return;
      category = btn.dataset.cat || "";
      shown = PAGE;
      renderChips();
      renderGrid();
    });
  }
  if (search) {
    search.addEventListener("input", function () {
      shown = PAGE;
      renderGrid();
    });
  }
  if (more) {
    more.addEventListener("click", function () {
      shown += PAGE;
      renderGrid();
    });
  }

  var hashId = (location.hash || "").replace("#", "");
  renderChips();
  renderGrid();
  if (hashId && itemById(hashId)) openItemModal(itemById(hashId).id);
}

function openItemModal(id) {
  var modal = document.getElementById("item-modal");
  if (!modal) return;
  var item = itemById(id);
  if (!item) return;

  document.getElementById("m-media").innerHTML = itemImage(item);
  document.getElementById("m-title").textContent = item.name;
  document.getElementById("m-sub").textContent = item.categoryLabel || "";

  function row(key, value) {
    return (
      '<div class="itemdb-info-row"><div class="key">' +
      escapeHtml(key) +
      '</div><div class="val">' +
      value +
      "</div></div>"
    );
  }

  function uniqTraderLines(list, priceKey) {
    var seen = {};
    var out = [];
    list.forEach(function (t) {
      var npc = t.npc || t.trader || "торговец";
      var price = t[priceKey];
      if (!price || price === "не продаёт" || price === "не покупает" || price === "—") return;
      var key = npc + "|" + price;
      if (seen[key]) return;
      seen[key] = true;
      out.push(
        '<span class="itemdb-tag">' +
          escapeHtml(npc) +
          " · " +
          escapeHtml(price) +
          "</span>"
      );
    });
    return out;
  }

  var traders =
    item.traders && item.traders.length
      ? item.traders
      : (GZ.PRICES || []).filter(function (price) {
          return price.id === item.id || price.id === item.classname;
        });

  var html = "";
  html += row("Редкость", '<span class="itemdb-tag">' + escapeHtml(item.rarity || "—") + "</span>");
  html += row("Где искать", escapeHtml(whereText(item)));

  if (item.recipe && item.recipe.length) {
    html += row(
      "Крафт",
      item.recipe
        .map(function (part) {
          var ing = itemById(part.id);
          return (
            '<span class="itemdb-tag">' +
            escapeHtml(ing ? ing.name : part.id) +
            " ×" +
            escapeHtml(part.qty || 1) +
            "</span>"
          );
        })
        .join("")
    );
  }

  var buyLines = uniqTraderLines(
    traders.filter(function (t) {
      return t.canBuy || (t.buy && t.buy !== "не продаёт" && t.buy !== "—");
    }),
    "buy"
  );
  var sellLines = uniqTraderLines(
    traders.filter(function (t) {
      return t.canSell || (t.sell && t.sell !== "не покупает" && t.sell !== "—");
    }),
    "sell"
  );
  if (buyLines.length) html += row("Купить у", buyLines.join(""));
  if (sellLines.length) html += row("Продать", sellLines.join(""));

  document.getElementById("m-body").innerHTML = html;
  modal.classList.add("open");
}

function closeItemModal() {
  var modal = document.getElementById("item-modal");
  if (modal) modal.classList.remove("open");
}

function initPricesPage() {
  var empty = document.getElementById("prices-empty");
  var tableWrap = document.getElementById("prices-table-wrap");
  var body = document.getElementById("prices-body");
  var search = document.getElementById("prices-search");
  if (!body) return;

  function render() {
    var q = ((search && search.value) || "").trim().toLowerCase();
    var rows = (GZ.PRICES || []).filter(function (row) {
      if (!q) return true;
      return (
        String(row.item || "").toLowerCase().indexOf(q) !== -1 ||
        String(row.trader || "").toLowerCase().indexOf(q) !== -1 ||
        String(row.id || "").toLowerCase().indexOf(q) !== -1
      );
    });
    if (!GZ.PRICES.length) {
      if (empty) empty.hidden = false;
      if (tableWrap) tableWrap.hidden = true;
      return;
    }
    if (empty) empty.hidden = true;
    if (tableWrap) tableWrap.hidden = false;
    body.innerHTML = rows
      .map(function (row) {
        var traderLabel = row.npc || row.trader || "—";
        if (row.shop && row.shop !== traderLabel) {
          traderLabel += " · " + row.shop;
        }
        return (
          "<tr><td>" +
          escapeHtml(row.item || row.id) +
          "</td><td>" +
          escapeHtml(traderLabel) +
          "</td><td>" +
          escapeHtml(row.buy || "—") +
          "</td><td>" +
          escapeHtml(row.sell || "—") +
          "</td></tr>"
        );
      })
      .join("");
  }

  if (search) search.addEventListener("input", render);
  render();
}

function initHomePage() {
  var box = document.getElementById("home-stats");
  if (!box) return;
  var status = GZ.STATUS || {};
  box.innerHTML =
    '<div class="stat">' +
    escapeHtml(status.items || Object.keys(GZ.ITEMS).length) +
    "<span>предметов</span></div><div class=\"stat\">" +
    escapeHtml(status.craftable || GZ.CRAFTABLE.length) +
    "<span>крафт</span></div><div class=\"stat\">" +
    escapeHtml(status.prices || GZ.PRICES.length) +
    "<span>цен</span></div>";
}

function initBgLoop() {
  var clips = Array.from(document.querySelectorAll(".bg-video__clip"));
  if (clips.length < 2) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var FADE_SEC = 1.4;
  var active = 0;
  var switching = false;

  clips.forEach(function (video) {
    video.muted = true;
    video.loop = false;
    video.playsInline = true;
  });

  var playSafe = function (video) {
    var p = video.play();
    if (p && typeof p.catch === "function") p.catch(function () {});
  };

  playSafe(clips[0]);

  var tick = function () {
    var current = clips[active];
    if (!current.duration || Number.isNaN(current.duration) || switching) {
      requestAnimationFrame(tick);
      return;
    }
    if (current.duration - current.currentTime <= FADE_SEC) {
      switching = true;
      var next = clips[1 - active];
      next.currentTime = 0;
      playSafe(next);
      next.classList.add("is-active");
      current.classList.remove("is-active");
      active = 1 - active;
      setTimeout(function () {
        current.pause();
        current.currentTime = 0;
        switching = false;
      }, FADE_SEC * 1000);
    }
    requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
}

document.addEventListener("DOMContentLoaded", function () {
  bootCatalog();
  initBgLoop();
  var page = document.body.dataset.page;
  if (page === "home") initHomePage();
  if (page === "craft") initCraftPage();
  if (page === "items") initItemsPage();
  if (page === "prices") initPricesPage();
  var modal = document.getElementById("item-modal");
  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target.id === "item-modal") closeItemModal();
    });
  }
});
