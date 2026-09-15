function toggleHeader() {
  var header = document.getElementById("full-header");
  var btn = document.querySelector(".menu-toggle");
  if (!header || !btn) return;
    header.classList.toggle("expanded");
    btn.setAttribute("aria-expanded", header.classList.contains("expanded") ? "true" : "false");
}

function initSparks() {
  const sparksContainer = document.querySelector(".sparks-container");
  if (!sparksContainer) return;

  function createSpark() {
    const spark = document.createElement("div");
    spark.classList.add("spark");

    const rand = Math.random();
    let sparkType, duration;
    if (rand < 0.55) {
      sparkType = "small";
      duration = 3 + Math.random() * 3;
    } else if (rand < 0.85) {
      sparkType = "medium";
      duration = 4 + Math.random() * 3;
    } else if (rand < 0.96) {
      sparkType = "large";
      duration = 5 + Math.random() * 4;
    } else {
      sparkType = "ember";
      duration = 7 + Math.random() * 5;
    }

    spark.classList.add(sparkType);
    spark.style.left = Math.random() * 100 + "%";
    const maxHeight = 60 + Math.random() * 35;
    const windDirection = (Math.random() - 0.5) * 2;
    const windStrength = 50 + Math.random() * 150;

    function getWindPoint(progress) {
      const baseWind = windDirection * windStrength * progress;
      const turbulence = (Math.sin(progress * Math.PI * 4) + Math.random() - 0.5) * 30;
      return baseWind + turbulence;
    }

    spark.style.setProperty("--wind-x-20", getWindPoint(0.2) + "px");
    spark.style.setProperty("--wind-y-20", -maxHeight * 0.2 + "vh");
    spark.style.setProperty("--rotate-20", Math.random() * 360 + "deg");
    spark.style.setProperty("--scale-20", 0.95 + Math.random() * 0.1);
    spark.style.setProperty("--wind-x-40", getWindPoint(0.4) + "px");
    spark.style.setProperty("--wind-y-40", -maxHeight * 0.4 + "vh");
    spark.style.setProperty("--rotate-40", Math.random() * 360 + "deg");
    spark.style.setProperty("--scale-40", 0.9 + Math.random() * 0.15);
    spark.style.setProperty("--wind-x-60", getWindPoint(0.6) + "px");
    spark.style.setProperty("--wind-y-60", -maxHeight * 0.6 + "vh");
    spark.style.setProperty("--rotate-60", Math.random() * 360 + "deg");
    spark.style.setProperty("--scale-60", 0.7 + Math.random() * 0.2);
    spark.style.setProperty("--wind-x-80", getWindPoint(0.8) + "px");
    spark.style.setProperty("--wind-y-80", -maxHeight * 0.8 + "vh");
    spark.style.setProperty("--rotate-80", Math.random() * 360 + "deg");
    spark.style.setProperty("--scale-80", 0.4 + Math.random() * 0.3);
    spark.style.setProperty("--wind-x-100", getWindPoint(1) + "px");
    spark.style.setProperty("--wind-y-100", -maxHeight + "vh");
    spark.style.setProperty("--rotate-100", Math.random() * 360 + "deg");

    const delay = Math.random() * 0.3;
    spark.style.animationDuration = duration + "s";
    spark.style.animationDelay = delay + "s";
    sparksContainer.appendChild(spark);
    setTimeout(() => spark.remove(), (duration + delay) * 1000);
  }

  function sparkBurst() {
    const count = 2 + Math.floor(Math.random() * 3);
    for (let i = 0; i < count; i++) setTimeout(() => createSpark(), i * 80);
  }

  function sparkLoop() {
    sparkBurst();
    setTimeout(sparkLoop, 150 + Math.random() * 250);
  }

  sparkLoop();
}

function itemById(id) {
  return GZ.ITEMS[id];
}

function hasExpandable(item) {
  return Boolean((item.recipe && item.recipe.length) || (item.tools && item.tools.length));
}

function collectTotals(itemId) {
  const item = itemById(itemId);
  const acc = {};
  (item.recipe || []).forEach((part) => {
    acc[part.id] = (acc[part.id] || 0) + part.qty;
  });
  return acc;
}

function initCraftPage() {
  const catalog = document.getElementById("catalog");
  const treeRoot = document.getElementById("tree-root");
  const infoRoot = document.getElementById("info-root");
  const search = document.getElementById("craft-search");
  const tooltip = document.getElementById("tooltip");
  if (!catalog || !treeRoot) return;

  let currentId = GZ.CRAFTABLE[0];
  let selectedId = currentId;

  function showTooltip(item, event) {
    if (!tooltip || !item) return;
    tooltip.innerHTML =
      "<strong>Где найти</strong><p>" +
      item.where +
      (item.qtyNote ? "</p><p class='note'>" + item.qtyNote : "") +
      "</p>";
    tooltip.classList.add("visible");
    moveTooltip(event);
  }

  function hideTooltip() {
    if (tooltip) tooltip.classList.remove("visible");
  }

  function moveTooltip(event) {
    if (!tooltip) return;
    const x = Math.min(event.clientX + 16, window.innerWidth - 340);
    const y = Math.min(event.clientY + 16, window.innerHeight - 160);
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
  }

  function renderInfo(id) {
    const item = itemById(id);
    if (!item || !infoRoot) return;
    const totals = collectTotals(currentId);
    const totalRows = Object.keys(totals)
      .map((key) => {
        const it = itemById(key);
        return (
          "<li><span>" +
          it.name +
          "</span><span>×" +
          totals[key] +
          "</span></li>"
        );
      })
      .join("");

    infoRoot.innerHTML =
      '<img src="' +
      item.image +
      '" alt="' +
      item.name +
      '">' +
      "<h3>" +
      item.name +
      "</h3>" +
      '<div class="muted">' +
      item.categoryLabel +
      (item.tool ? " · не расходуется" : "") +
      "</div>" +
      '<div class="info-label">Описание</div>' +
      "<p>" +
      item.description +
      "</p>" +
      '<div class="info-label">Где найти</div>' +
      "<p>" +
      item.where +
      "</p>" +
      (item.qtyNote ? "<p class='note'>" + item.qtyNote + "</p>" : "") +
      '<div class="totals"><div class="info-label">Нужно для станка</div><ul>' +
      totalRows +
      "</ul></div>";
  }

  function renderNode(part, multiplier) {
    const item = itemById(part.id);
    if (!item) return "";
    const qty = part.qty * multiplier;
    const expandable = hasExpandable(item);
    const toolMark = item.tool ? '<span class="tool-tag">инструмент</span>' : "";
    const children = [];
    if (item.recipe) {
      item.recipe.forEach((child) => children.push(renderNode(child, qty)));
    }
    if (item.tools) {
      item.tools.forEach((child) => children.push(renderNode(child, 1)));
    }

    return (
      '<div class="tree-node' +
      (expandable ? "" : "") +
      '" data-id="' +
      item.id +
      '">' +
      '<div class="tree-row' +
      (selectedId === item.id ? " selected" : "") +
      '" data-id="' +
      item.id +
      '">' +
      '<button class="tree-toggle' +
      (expandable ? "" : " leaf") +
      '" type="button" aria-label="Раскрыть">' +
      (expandable ? "+" : "") +
      "</button>" +
      '<img src="' +
      item.image +
      '" alt="' +
      item.name +
      '">' +
      '<div class="tree-meta"><div class="tree-name">' +
      item.name +
      (item.tool ? " " : "") +
      toolMark +
      '</div><div class="tree-sub">' +
      item.categoryLabel +
      (expandable ? " · есть крафт" : "") +
      "</div></div>" +
      '<div class="tree-qty">×' +
      qty +
      "</div></div>" +
      (expandable ? '<div class="tree-children">' + children.join("") + "</div>" : "") +
      "</div>"
    );
  }

  function renderTree() {
    const item = itemById(currentId);
    if (!item) return;
    const nodes = (item.recipe || []).map((part) => renderNode(part, 1)).join("");
    treeRoot.innerHTML =
      '<div class="tree-result">' +
      '<img src="' +
      item.image +
      '" alt="' +
      item.name +
      '">' +
      "<div><h3>" +
      item.name +
      "</h3><p class='muted'>" +
      item.description +
      "</p></div></div>" +
      '<p class="tree-hint">Наведите на компонент, чтобы увидеть, где его искать. Нажмите на строку с «+», чтобы раскрыть ветку крафта.</p>' +
      '<div class="tree-list">' +
      nodes +
      "</div>";
    renderInfo(selectedId);
  }

  function renderCatalog(filter) {
    const q = (filter || "").trim().toLowerCase();
    catalog.innerHTML = GZ.CRAFTABLE.map((id) => {
      const item = itemById(id);
      if (q && !item.name.toLowerCase().includes(q)) return "";
      return (
        '<button class="catalog-item' +
        (id === currentId ? " active" : "") +
        '" data-id="' +
        id +
        '">' +
        '<img src="' +
        item.image +
        '" alt="">' +
        "<div><strong>" +
        item.name +
        "</strong><span>" +
        item.categoryLabel +
        " · " +
        item.recipe.length +
        " компонентов</span></div></button>"
      );
    }).join("");
  }

  catalog.addEventListener("click", (event) => {
    const btn = event.target.closest(".catalog-item");
    if (!btn) return;
    currentId = btn.dataset.id;
    selectedId = currentId;
    renderCatalog(search.value);
    renderTree();
  });

  treeRoot.addEventListener("click", (event) => {
    hideTooltip();
    const toggle = event.target.closest(".tree-toggle");
    const row = event.target.closest(".tree-row");
    if (toggle && !toggle.classList.contains("leaf")) {
      event.preventDefault();
      const node = toggle.closest(".tree-node");
      node.classList.toggle("open");
      toggle.textContent = node.classList.contains("open") ? "−" : "+";
    }
    if (row) {
      selectedId = row.dataset.id;
      treeRoot.querySelectorAll(".tree-row").forEach((el) => el.classList.remove("selected"));
      row.classList.add("selected");
      renderInfo(selectedId);
      if (window.innerWidth < 980 && infoRoot) {
        infoRoot.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  });

  treeRoot.addEventListener("mouseover", (event) => {
    const row = event.target.closest(".tree-row");
    if (!row) return;
    showTooltip(itemById(row.dataset.id), event);
  });

  treeRoot.addEventListener("mousemove", (event) => {
    if (event.target.closest(".tree-row")) moveTooltip(event);
  });

  treeRoot.addEventListener("mouseleave", hideTooltip);

  if (search) {
    search.addEventListener("input", () => renderCatalog(search.value));
  }

  const hashId = (location.hash || "").replace("#", "");
  if (hashId && GZ.ITEMS[hashId]) {
    currentId = hashId;
    selectedId = hashId;
  }

  renderCatalog("");
  renderTree();
}

document.addEventListener("DOMContentLoaded", () => {
  initSparks();
  if (document.body.dataset.page === "craft") initCraftPage();
});
