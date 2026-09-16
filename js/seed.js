window.GZ = window.GZ || {};

GZ.SEED_ITEMS = {
  vest_6b45: {
    id: "vest_6b45",
    classname: "vest_6b45",
    name: "Бронежилет тактический 6Б45",
    category: "armor",
    categoryLabel: "Броня",
    image: "img/items/vest-6b45.jpg",
    craftable: true,
    description:
      "Тяжёлый тактический бронежилет. Собирается на станке крафта. Даёт серьёзную защиту, но требует редкие военные детали и полный набор расходников.",
    where:
      "Не лутается в готовом виде — только крафт на станке. Соберите все компоненты и используйте кнопку «Крафт».",
    tier: "—",
    rarity: "крафт",
    recipe: [
      { id: "plate_carrier", qty: 1 },
      { id: "cloth", qty: 100 },
      { id: "armor_plate", qty: 20 },
      { id: "rope", qty: 2 },
      { id: "metal_plate", qty: 10 },
      { id: "duct_tape", qty: 100 },
      { id: "sewing_kit", qty: 100 }
    ]
  },
  plate_carrier: {
    id: "plate_carrier",
    classname: "PlateCarrierVest",
    name: "Бронежилет",
    category: "armor",
    categoryLabel: "Броня",
    image: "img/items/plate-carrier.jpg",
    description: "Основа для сборки 6Б45. Без неё жилет не скрафтить.",
    where:
      "Военные локации Черноруси: СЗ аэродром, Тисы, Каменск, военка Павлово и Зеленогорска, тюрьма на острове. Также крушения вертолётов и редкие военные события сервера.",
    tier: "Tier3",
    rarity: "редкий"
  },
  cloth: {
    id: "cloth",
    classname: "cloth",
    name: "Защитный компонент",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/cloth.jpg",
    qtyNote: "Нужен полный запас — 100 единиц.",
    description: "Защитный материал для обшивки бронежилета.",
    where: "Жилые дома, шкафы, склады, военные и промышленные точки. Для рецепта нужен полный запас на 100 единиц.",
    rarity: "обычный"
  },
  armor_plate: {
    id: "armor_plate",
    classname: "armor_plate",
    name: "Бронепластина",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/armor-plate.jpg",
    description: "Баллистические пластины. На один 6Б45 нужно сразу 20 штук.",
    where:
      "Военные базы высокого уровня: Тисы, СЗ аэродром, Каменск, укреплённые точки. Иногда стоят уже внутри найденных бронежилетов.",
    rarity: "редкий"
  },
  rope: {
    id: "rope",
    classname: "Rope",
    name: "Паракорд",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/rope.jpg",
    description: "Прочный паракорд. Для жилета нужно две штуки.",
    where: "Ищется в схронах. Также встречается в сараях, на фермах, в промзонах и гаражах.",
    rarity: "обычный"
  },
  metal_plate: {
    id: "metal_plate",
    classname: "MetalPlate",
    name: "Лист металла",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/metal-plate.jpg",
    description: "Профлист. На жилет нужно 10 листов.",
    where: "Разберите металлические конструкции пассатижами: заборы, сараи, гаражи, ангары, крыши промзон.",
    rarity: "обычный"
  },
  duct_tape: {
    id: "duct_tape",
    classname: "DuctTape",
    name: "Изолента",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/duct-tape.jpg",
    qtyNote: "Нужен полный моток — 100 единиц прочности.",
    description: "Армированный скотч. В рецепт идёт целый моток.",
    where: "Гаражи, сараи с инструментами, склады, стройки, заправки, хозяйственные магазины, багажники машин.",
    rarity: "обычный"
  },
  sewing_kit: {
    id: "sewing_kit",
    classname: "SewingKit",
    name: "Набор для шитья",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/sewing-kit.jpg",
    qtyNote: "Нужен полный набор — 100 единиц.",
    description: "Швейный набор. В рецепт идёт целиком.",
    where: "Жилые дома — спальни и шкафы, магазины одежды, школы, офисы, иногда больницы.",
    rarity: "обычный"
  }
};

GZ.SEED_CRAFTABLE = ["vest_6b45"];
GZ.SEED_PRICES = [];
GZ.SEED_STATUS = {
  generatedAt: "",
  items: 8,
  craftable: 1,
  prices: 0,
  lootRows: 0,
  icons: 8,
  missing: ["Пока показан пример 6Б45. Положите файлы сервера в incoming и запустите tools\\собрать.bat"],
  fromServer: false
};
