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
  if (src.indexOf("?") === -1) src += "?v=3";
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
  if (!item) return "—";

  var rarity = String(item.rarity || "");
  if (
    rarity === "не встречается на карте" ||
    rarity === "у торговца" ||
    rarity === "крафт / у торговца"
  ) {
    return "—";
  }
  if (rarity === "можно скрафтить") {
    var craftWhere = String(item.where || "").trim();
    if (craftWhere.indexOf("Крафт") === 0) return craftWhere;
    return "—";
  }

  var nominal = item.nominal;
  if (nominal === 0 || nominal === "0") return "—";

  var places = [];
  var seen = {};
  (item.loot || []).forEach(function (zone) {
    var house = zone && zone.house;
    if (!house || seen[house]) return;
    seen[house] = true;
    places.push(house);
  });
  if (places.length && nominal != null && Number(nominal) > 0) {
    return places.slice(0, 4).join(", ");
  }

  var raw = String(item.where || "").trim();
  if (!raw || raw === "—" || raw.indexOf("В файлах сервера") === 0) return "—";

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
    .trim() || "—";
}

function itemTraders(item) {
  if (!item) return [];
  if (item.traders && item.traders.length) return item.traders;
  return (GZ.PRICES || []).filter(function (price) {
    return price.id === item.id || price.id === item.classname;
  });
}

function itemBuyPrice(item) {
  var traders = itemTraders(item);
  for (var i = 0; i < traders.length; i++) {
    var t = traders[i];
    if (!t) continue;
    if (t.canBuy || (t.buy && t.buy !== "не продаёт" && t.buy !== "—")) {
      if (t.buy && t.buy !== "не продаёт" && t.buy !== "—") return t.buy;
    }
  }
  return "";
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
    out.push(escapeHtml(npc) + " · " + escapeHtml(price));
  });
  return out;
}

function buildItemPreviewHtml(item) {
  if (!item) return "";
  var traders = itemTraders(item);
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
  var html =
    "<strong>" +
    escapeHtml(item.name || "Предмет") +
    "</strong>" +
    '<p class="tooltip-meta">' +
    escapeHtml(item.categoryLabel || "—") +
    (item.rarity ? " · " + escapeHtml(item.rarity) : "") +
    "</p>";
  if (item.description) {
    html += "<p>" + escapeHtml(item.description) + "</p>";
  }
  var buyPrice = itemBuyPrice(item);
  if (buyPrice) {
    html += "<p><b>Цена:</b> " + escapeHtml(buyPrice) + "</p>";
  }
  html += "<p><b>Где искать:</b> " + escapeHtml(whereText(item)) + "</p>";
  if (item.recipe && item.recipe.length) {
    html +=
      "<p><b>Крафт:</b> " +
      item.recipe
        .map(function (part) {
          var ing = itemById(part.id);
          return escapeHtml(ing ? ing.name : part.id) + " ×" + escapeHtml(part.qty || 1);
        })
        .join(", ") +
      "</p>";
  }
  if (buyLines.length) html += "<p><b>Купить у:</b> " + buyLines.join("; ") + "</p>";
  if (sellLines.length) html += "<p><b>Продать:</b> " + sellLines.join("; ") + "</p>";
  return html;
}

function moveFloatingTooltip(tooltip, event, width) {
  if (!tooltip) return;
  var w = width || 340;
  var x = Math.min(event.clientX + 16, window.innerWidth - w - 12);
  var y = Math.min(event.clientY + 16, window.innerHeight - 24);
  var rectH = tooltip.offsetHeight || 180;
  if (y + rectH > window.innerHeight - 12) {
    y = Math.max(12, event.clientY - rectH - 12);
  }
  tooltip.style.left = Math.max(8, x) + "px";
  tooltip.style.top = Math.max(8, y) + "px";
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

  var currentId = null;
  var expanded = false;
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
    moveFloatingTooltip(tooltip, event, 340);
  }

  function renderNode(part, multiplier, ancestors) {
    var item = itemById(part.id) || {
      id: part.id,
      name: part.id,
      categoryLabel: "Компонент",
      image: ""
    };
    var nodeId = String(item.id || part.id);
    var chain = ancestors || [];
    var looping = chain.indexOf(nodeId) !== -1;
    var qty = (part.qty || 1) * multiplier;
    var expandable = !looping && hasExpandable(item);
    var toolMark = item.tool ? '<span class="tool-tag">инструмент</span>' : "";
    var children = [];
    if (expandable) {
      var nextChain = chain.concat([nodeId]);
      (item.recipe || []).forEach(function (child) {
        children.push(renderNode(child, qty, nextChain));
      });
      (item.tools || []).forEach(function (child) {
        children.push(renderNode(child, 1, nextChain));
      });
    }

    return (
      '<div class="tree-node" data-id="' +
      escapeHtml(nodeId) +
      '"><div class="tree-row" data-id="' +
      escapeHtml(nodeId) +
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
      (expandable ? " · есть крафт" : looping ? " · уже в цепочке" : "") +
      '</div></div><div class="tree-qty">×' +
      escapeHtml(qty) +
      "</div></div>" +
      (expandable ? '<div class="tree-children">' + children.join("") + "</div>" : "") +
      "</div>"
    );
  }

  function renderTree() {
    var item = itemById(currentId);
    if (!item) {
      treeRoot.innerHTML = "";
      return;
    }
    var nodes = "";
    try {
      nodes = (item.recipe || [])
        .map(function (part) {
          return renderNode(part, 1, [String(item.id)]);
        })
        .join("");
    } catch (err) {
      treeRoot.innerHTML =
        '<div class="tree-result">' +
        itemImage(item) +
        "<div><h3>" +
        escapeHtml(item.name) +
        '</h3><p class="muted">Не удалось построить дерево рецепта.</p></div></div>';
      return;
    }
    treeRoot.innerHTML =
      '<div class="tree-result">' +
      itemImage(item) +
      "<div><h3>" +
      escapeHtml(item.name) +
      "</h3><p class='muted'>" +
      escapeHtml(item.description || whereText(item)) +
      "</p></div></div>" +
      '<p class="tree-hint">Наведите на компонент, чтобы увидеть, где его искать. Повторный клик по предмету свернёт рецепт.</p>' +
      (nodes
        ? '<div class="tree-list">' + nodes + "</div>"
        : '<div class="empty-state"><p class="muted">Рецепт для этого предмета ещё не найден в файлах админа.</p></div>');
  }

  function placeTreeAfterSelected() {
    var slot = document.getElementById("craft-expand-slot");
    if (!slot || !treeRoot) return;
    if (treeRoot.parentElement !== slot) {
      slot.appendChild(treeRoot);
    }
    treeRoot.hidden = false;
    treeRoot.classList.add("is-expanded");
  }

  function hideCraftTree() {
    if (!treeRoot) return;
    treeRoot.hidden = true;
    treeRoot.classList.remove("is-expanded");
    if (catalog.contains(treeRoot)) {
      catalog.after(treeRoot);
    }
  }

  function renderChips() {
    if (!chips) return;
    var useToc = chips.classList.contains("book-toc");
    var html = useToc
      ? '<button type="button" class="book-toc__row' +
        (!category ? " is-active" : "") +
        '" data-cat=""><span class="book-toc__name">Все рецепты</span><span class="book-toc__dots" aria-hidden="true"></span><span class="book-toc__num">—</span></button>'
      : '<button type="button" class="chip' +
        (!category ? " active" : "") +
        '" data-cat="">Все</button>';
    categoryOrder().forEach(function (name, index) {
      var count = (categoryMap[name] || []).length;
      var n = index + 1;
      var num = n < 10 ? "0" + n : String(n);
      if (useToc) {
        html +=
          '<button type="button" class="book-toc__row' +
          (category === name ? " is-active" : "") +
          '" data-cat="' +
          escapeHtml(name) +
          '"><span class="book-toc__name">' +
          escapeHtml(name) +
          '</span><span class="book-toc__dots" aria-hidden="true"></span><span class="book-toc__num">' +
          num +
          "</span></button>";
      } else {
        html +=
          '<button type="button" class="chip' +
          (category === name ? " active" : "") +
          '" data-cat="' +
          escapeHtml(name) +
          '">' +
          escapeHtml(name) +
          (count ? " · " + count : "") +
          "</button>";
      }
    });
    chips.innerHTML = html;
  }

  function renderCatalog() {
    if (treeRoot && catalog.contains(treeRoot)) {
      treeRoot.hidden = true;
      catalog.after(treeRoot);
    }

    var list = filteredIds();
    if (!list.length) {
      catalog.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1"><p class="muted">В этой категории ничего не найдено.</p></div>';
      hideCraftTree();
      return;
    }
    if (expanded && currentId && list.indexOf(currentId) === -1) {
      expanded = false;
      currentId = null;
    }
    catalog.innerHTML = list
      .map(function (id) {
        var item = itemById(id);
        if (!item) return "";
        var parts = (item.recipe && item.recipe.length) || 0;
        var isOpen = expanded && id === currentId;
        var tile =
          '<button class="item-tile' +
          (isOpen ? " active" : "") +
          '" type="button" data-id="' +
          escapeHtml(id) +
          '" aria-expanded="' +
          (isOpen ? "true" : "false") +
          '"><span class="badge">' +
          escapeHtml(parts ? parts + " комп." : "крафт") +
          '</span><span class="img-box">' +
          itemImage(item) +
          '</span><span class="label">' +
          escapeHtml(item.name) +
          "</span></button>";
        if (isOpen) {
          tile += '<div class="craft-expand" id="craft-expand-slot"></div>';
        }
        return tile;
      })
      .join("");
    if (expanded && currentId) {
      placeTreeAfterSelected();
      renderTree();
    } else {
      hideCraftTree();
    }
  }

  if (chips) {
    chips.addEventListener("click", function (event) {
      var btn = event.target.closest(".chip, .book-toc__row");
      if (!btn) return;
      category = btn.dataset.cat || "";
      expanded = false;
      currentId = null;
      renderChips();
      renderCatalog();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  catalog.addEventListener("click", function (event) {
    var btn = event.target.closest(".item-tile");
    if (!btn) return;
    var id = btn.dataset.id;
    var scrollY = window.scrollY;
    if (expanded && currentId === id) {
      expanded = false;
      currentId = null;
    } else {
      currentId = id;
      expanded = true;
    }
    renderCatalog();
    window.scrollTo(0, scrollY);
    var active = catalog.querySelector(".item-tile.active");
    if (active) {
      var rect = active.getBoundingClientRect();
      var headerOffset = 120;
      if (rect.top < headerOffset || rect.bottom > window.innerHeight) {
        active.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    }
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
    });
  }

  var hashId = (location.hash || "").replace("#", "");
  if (hashId && itemById(hashId) && GZ.CRAFTABLE.indexOf(itemById(hashId).id) !== -1) {
    currentId = itemById(hashId).id;
    expanded = true;
    var hashItem = itemById(hashId);
    category = itemCategory(hashItem) || "";
  }

  renderChips();
  renderCatalog();
}

function initItemsPage() {
  var grid = document.getElementById("items-grid");
  var search = document.getElementById("items-search");
  var chips = document.getElementById("items-chips");
  var more = document.getElementById("items-more");
  var tooltip = document.getElementById("tooltip");
  if (!grid) return;

  var PAGE = 60;
  var shown = PAGE;
  var categoryKey = "";
  var categoryLabel = "";

  function allItems() {
    return Object.keys(GZ.ITEMS)
      .map(function (id) {
        return GZ.ITEMS[id];
      })
      .filter(function (item) {
        if (!item) return false;
        // book=false — заражённые, животные, AI, без иконок и т.п.
        if (item.book === false) return false;
        var cn = String(item.classname || item.id || "").toLowerCase();
        var name = String(item.name || "").toLowerCase();
        if (
          cn.indexOf("zmb") !== -1 ||
          cn.indexOf("zombie") !== -1 ||
          cn.indexOf("ecolog") !== -1 ||
          cn.indexOf("creature_urban3") !== -1 ||
          cn.indexOf("evg_") === 0 ||
          name.indexOf("инфицирован") !== -1 ||
          name.indexOf("зараженн") !== -1 ||
          name.indexOf("заражённ") !== -1 ||
          name === "курильщик" ||
          (name.indexOf("ворот") !== -1 && name.indexOf("воротник") === -1) ||
          name.indexOf("лестниц") !== -1 ||
          name.indexOf("тент") !== -1 ||
          name === "маленькое окно" ||
          name === "окно" ||
          name === "медсестра" ||
          name.indexOf("могильный крест") !== -1 ||
          name.indexOf("пистолетный кейс") !== -1 ||
          name.indexOf("площадка для укрытия") !== -1 ||
          name.indexOf("поддон") !== -1 ||
          name === "стена" ||
          name === "столб" ||
          name === "набор для стены" ||
          name === "набор для столба" ||
          name === "пол" ||
          name === "набор для пола" ||
          name.indexOf("ракушк") !== -1 ||
          name === "рампа" ||
          name.indexOf("набор для изготовления рампы") !== -1 ||
          name.indexOf("сборщик дождя") !== -1 ||
          name.indexOf("свернутый календар") !== -1 ||
          name.indexOf("свёрнутый календар") !== -1 ||
          name.indexOf("brdk house") !== -1 ||
          name.indexOf("вагон") !== -1 ||
          name.indexOf("power wagon") !== -1 ||
          name.indexOf("evg ") === 0 ||
          name.indexOf("evg_") === 0
        ) {
          return false;
        }
        var img = String(item.image || "").trim();
        if (!img) {
          // резиновые лодки без картинки — скрыть даже в «Авто»
          if (name === "резиновая лодка") return false;
          if (name.indexOf("спортивная сумка") !== -1) return false;
          if (name.indexOf("куртка") !== -1) return false;
          if (name.indexOf("тактический ремень") !== -1) return false;
          if (cn.indexOf("loftd_") === 0) return false;
          if (item.categoryLabel === "Прочее") return false;
          // машины в «Авто» можно без картинки; остальное — нет
          return item.categoryLabel === "Авто" || item.category === "vehicles";
        }
        return true;
      })
      .sort(function (a, b) {
        return (a.name || "").localeCompare(b.name || "", "ru");
      });
  }

  function filtered() {
    var q = ((search && search.value) || "").trim().toLowerCase();
    return allItems().filter(function (item) {
      if (categoryKey || categoryLabel) {
        if (categoryLabel) {
          if (item.categoryLabel !== categoryLabel) return false;
        } else if (item.category !== categoryKey) {
          return false;
        }
      }
      if (!q) return true;
      return (
        (item.name || "").toLowerCase().indexOf(q) !== -1 ||
        String(item.classname || "").toLowerCase().indexOf(q) !== -1
      );
    });
  }

  function renderChips() {
    if (!chips) return;
    var byLabel = {};
    allItems().forEach(function (item) {
      var label = item.categoryLabel;
      if (!label) return;
      if (!byLabel[label]) byLabel[label] = item.category || label;
    });
    // «Авто» всегда первой тематической строкой после «Все»
    var labels = Object.keys(byLabel).sort(function (a, b) {
      if (a === "Авто") return -1;
      if (b === "Авто") return 1;
      return a.localeCompare(b, "ru");
    });
    var html =
      '<button type="button" class="book-toc__row' +
      (!categoryKey && !categoryLabel ? " is-active" : "") +
      '" data-cat="" data-label=""><span class="book-toc__name">Все предметы</span><span class="book-toc__dots" aria-hidden="true"></span><span class="book-toc__num">—</span></button>';
    labels.forEach(function (label, index) {
      var key = byLabel[label];
      var n = index + 1;
      var num = n < 10 ? "0" + n : String(n);
      var active = categoryLabel === label;
      html +=
        '<button type="button" class="book-toc__row' +
        (active ? " is-active" : "") +
        '" data-cat="' +
        escapeHtml(key) +
        '" data-label="' +
        escapeHtml(label) +
        '"><span class="book-toc__name">' +
        escapeHtml(label) +
        '</span><span class="book-toc__dots" aria-hidden="true"></span><span class="book-toc__num">' +
        num +
        "</span></button>";
    });
    chips.innerHTML = html;
  }

  function renderGrid() {
    var list = filtered();
    if (!list.length) {
      grid.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1"><h3>Ничего не найдено</h3><p class="muted">Измените поиск.</p></div>';
      if (more) more.hidden = true;
      return;
    }
    grid.innerHTML = list
      .slice(0, shown)
      .map(function (item) {
        return (
          '<button class="item-tile" type="button" data-id="' +
          escapeHtml(item.id) +
          '">' +
          '<span class="img-box">' +
          itemImage(item) +
          '</span><span class="label">' +
          escapeHtml(item.name) +
          "</span></button>"
        );
      })
      .join("");
    if (more) more.hidden = list.length <= shown;
  }

  function hideTooltip() {
    if (tooltip) tooltip.classList.remove("visible");
  }

  function showItemTooltip(item, event) {
    if (!tooltip || !item) return;
    tooltip.classList.add("tooltip--rich");
    tooltip.innerHTML = buildItemPreviewHtml(item);
    tooltip.classList.add("visible");
    moveFloatingTooltip(tooltip, event, 360);
  }

  grid.addEventListener("click", function (event) {
    var tile = event.target.closest(".item-tile");
    if (tile) openItemModal(tile.dataset.id);
  });
  grid.addEventListener("mouseover", function (event) {
    var tile = event.target.closest(".item-tile");
    if (!tile || !tooltip) return;
    if (tooltip.dataset.id === tile.dataset.id && tooltip.classList.contains("visible")) return;
    tooltip.dataset.id = tile.dataset.id;
    showItemTooltip(itemById(tile.dataset.id), event);
  });
  grid.addEventListener("mousemove", function (event) {
    if (!tooltip || !tooltip.classList.contains("visible")) return;
    if (event.target.closest(".item-tile")) moveFloatingTooltip(tooltip, event, 360);
  });
  grid.addEventListener("mouseleave", hideTooltip);

  if (chips) {
    chips.addEventListener("click", function (event) {
      var btn = event.target.closest(".book-toc__row, .chip");
      if (!btn) return;
      categoryKey = btn.getAttribute("data-cat") || "";
      categoryLabel = btn.getAttribute("data-label") || "";
      shown = PAGE;
      hideTooltip();
      renderChips();
      renderGrid();
    });
  }
  if (search) {
    search.addEventListener("input", function () {
      shown = PAGE;
      hideTooltip();
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

  var traders = itemTraders(item);
  var html = "";
  var buyPrice = itemBuyPrice(item);
  if (buyPrice) {
    html += row("Цена", '<span class="itemdb-tag">' + escapeHtml(buyPrice) + "</span>");
  }
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
  ).map(function (line) {
    return '<span class="itemdb-tag">' + line + "</span>";
  });
  var sellLines = uniqTraderLines(
    traders.filter(function (t) {
      return t.canSell || (t.sell && t.sell !== "не покупает" && t.sell !== "—");
    }),
    "sell"
  ).map(function (line) {
    return '<span class="itemdb-tag">' + line + "</span>";
  });
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
  if (box) {
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
  initSurvivorJournal();
}

function initSurvivorJournal() {
  var openBtn = document.getElementById("journal-open");
  var modal = document.getElementById("journal-modal");
  var bookWrap = document.querySelector(".journal-book-wrap");
  var bookEl = document.getElementById("survivor-book");
  var introEl = document.getElementById("journal-intro");
  var introOpenBtn = document.getElementById("journal-intro-open");
  var hintEl = document.getElementById("journal-hint");
  if (!openBtn || !modal || !bookWrap || !bookEl || !window.St || !St.PageFlip) return;

  var pageFlip = null;
  var pagesHtml = bookEl.innerHTML;
  var prevBtn = document.getElementById("journal-prev");
  var nextBtn = document.getElementById("journal-next");
  var lastFocus = null;
  var onCover = true;

  function ensureBookElement() {
    bookEl = document.getElementById("survivor-book");
    if (bookEl) return bookEl;
    bookEl = document.createElement("div");
    bookEl.id = "survivor-book";
    bookEl.className = "journal-book";
    bookEl.innerHTML = pagesHtml;
    bookWrap.insertBefore(bookEl, nextBtn || null);
    return bookEl;
  }

  function bookSize() {
    var maxW = Math.min(window.innerWidth - 120, 980);
    var pageW = Math.floor(maxW / 2);
    pageW = Math.max(160, Math.min(pageW, 460));
    if (window.innerWidth < 640) {
      pageW = Math.max(150, Math.min(window.innerWidth - 88, 280));
    }
    var pageH = Math.round(pageW * 1.28);
    var maxH = window.innerHeight - 160;
    if (pageH > maxH) {
      pageH = maxH;
      pageW = Math.round(pageH / 1.28);
    }
    return { width: pageW, height: pageH };
  }

  function setCoverMode(enabled) {
    onCover = enabled;
    document.body.classList.toggle("journal-on-cover", enabled);
    if (introEl) introEl.hidden = !enabled;
    if (bookEl) bookEl.hidden = enabled;
    if (hintEl) {
      hintEl.textContent = enabled
        ? "Нажми на обложку или стрелку, чтобы открыть · Esc — закрыть"
        : "Тяни за угол страницы или жми стрелки · Esc — закрыть";
    }
    if (prevBtn) prevBtn.disabled = enabled;
    if (nextBtn) nextBtn.disabled = false;
  }

  function updateChrome() {
    if (onCover || !pageFlip) return;
    var idx = pageFlip.getCurrentPageIndex();
    var count = pageFlip.getPageCount();
    if (prevBtn) prevBtn.disabled = idx <= 0;
    if (nextBtn) nextBtn.disabled = idx >= count - 1;
  }

  function destroyBook() {
    if (pageFlip) {
      try {
        pageFlip.destroy();
      } catch (e) {}
      pageFlip = null;
    }
    bookEl = ensureBookElement();
    bookEl.innerHTML = pagesHtml;
    bookEl.hidden = true;
  }

  function createBook(startPage) {
    var keepPage = typeof startPage === "number" ? startPage : 0;
    destroyBook();
    bookEl.hidden = false;
    var size = bookSize();
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    pageFlip = new St.PageFlip(bookEl, {
      width: size.width,
      height: size.height,
      size: "fixed",
      minWidth: 140,
      maxWidth: 500,
      minHeight: 180,
      maxHeight: 680,
      drawShadow: true,
      flippingTime: reduced ? 200 : 850,
      usePortrait: window.innerWidth < 720,
      startZIndex: 5,
      autoSize: true,
      maxShadowOpacity: 0.35,
      showCover: false,
      mobileScrollSupport: false,
      useMouseEvents: true,
      swipeDistance: 30,
      clickEventForward: true,
      disableFlipByClick: false
    });
    pageFlip.loadFromHTML(bookEl.querySelectorAll(".journal-page"));
    pageFlip.on("flip", updateChrome);
    pageFlip.on("changeState", updateChrome);
    if (keepPage > 0) pageFlip.turnToPage(keepPage);
    updateChrome();
  }

  function openPages() {
    if (!onCover) return;
    setCoverMode(false);
    createBook(0);
  }

  function openJournal() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("journal-open");
    destroyBook();
    setCoverMode(true);
    var closeBtn = modal.querySelector(".journal-modal__close");
    if (closeBtn) closeBtn.focus();
  }

  function closeJournal() {
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("journal-open");
    document.body.classList.remove("journal-on-cover");
    destroyBook();
    setCoverMode(true);
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
  }

  function goNext() {
    if (onCover) {
      openPages();
      return;
    }
    if (pageFlip) pageFlip.flipNext("bottom");
  }

  function goPrev() {
    if (onCover) return;
    if (!pageFlip) return;
    if (pageFlip.getCurrentPageIndex() <= 0) {
      destroyBook();
      setCoverMode(true);
      return;
    }
    pageFlip.flipPrev("bottom");
  }

  openBtn.addEventListener("click", openJournal);
  if (introOpenBtn) introOpenBtn.addEventListener("click", openPages);
  modal.querySelectorAll("[data-journal-close]").forEach(function (el) {
    el.addEventListener("click", closeJournal);
  });
  if (prevBtn) prevBtn.addEventListener("click", goPrev);
  if (nextBtn) nextBtn.addEventListener("click", goNext);

  document.addEventListener("keydown", function (event) {
    if (modal.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeJournal();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      goPrev();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      goNext();
    }
  });

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    if (modal.hidden || onCover || !pageFlip) return;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      createBook(pageFlip ? pageFlip.getCurrentPageIndex() : 0);
    }, 180);
  });
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
