window.GZ = window.GZ || {};

GZ.ITEMS = {
  vest_6b45: {
    id: "vest_6b45",
    name: "Бронежилет тактический 6Б45",
    category: "armor",
    categoryLabel: "Броня",
    image: "img/items/vest-6b45.jpg",
    craftable: true,
    description:
      "Тяжёлый тактический бронежилет. Собирается на станке крафта. Даёт серьёзную защиту, но требует редкие военные детали и полный набор расходников.",
    where:
      "Не лутается в готовом виде — только крафт на станке. Соберите все компоненты и используйте кнопку «Крафт».",
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
    name: "Плитоноска",
    category: "armor",
    categoryLabel: "Броня",
    image: "img/items/plate-carrier.jpg",
    description: "Основа жилета. Без неё 6Б45 не собрать.",
    where:
      "Военные локации Черноруси: СЗ аэродром, Тисы, Каменск, военка Павлово и Зеленогорска, тюрьма на острове. Также крушения вертолётов и редкие военные события сервера."
  },

  cloth: {
    id: "cloth",
    name: "Ткань",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/cloth.jpg",
    qtyNote: "Нужен полный рулон — 100 единиц.",
    description: "Рулон ткани для обшивки бронежилета.",
    where:
      "Жилые дома, шкафы, магазины одежды, склады. Часто получается из одежды: разрежьте куртки, штаны и футболки ножом. Для рецепта нужен полный запас на 100 единиц."
  },

  armor_plate: {
    id: "armor_plate",
    name: "Пластина для брони",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/armor-plate.jpg",
    description: "Баллистические пластины. На один 6Б45 нужно сразу 20 штук.",
    where:
      "Военные базы высокого уровня: Тисы, СЗ аэродром, Каменск, укреплённые точки. Иногда стоят уже внутри найденных плитоносок. Ищите в оружейных и на крушениях."
  },

  rope: {
    id: "rope",
    name: "Верёвка",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/rope.jpg",
    craftable: true,
    description: "Паракорд. Для жилета нужно две штуки.",
    where:
      "Сараи, фермы, промышленные здания, гаражи, лодочные станции. Можно скрафтить из 6 тряпок. Запасной путь — верёвка из кишок животных после охоты.",
    recipe: [{ id: "rags", qty: 6 }]
  },

  metal_plate: {
    id: "metal_plate",
    name: "Лист металла",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/metal-plate.jpg",
    description: "Профлист. На жилет нужно 10 листов.",
    where:
      "Разберите металлические конструкции пассатижами: заборы, сараи, гаражи, ангары, крыши промзон. Также лежит на стройках, складах и в индустриальных районах."
  },

  duct_tape: {
    id: "duct_tape",
    name: "Изолента",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/duct-tape.jpg",
    qtyNote: "Нужен полный моток — 100 единиц прочности.",
    description: "Армированный скотч. В рецепт идёт целый моток.",
    where:
      "Гаражи, сараи с инструментами, склады, стройки, заправки, хозяйственные магазины, багажники машин. Берите полный моток: в крафт уходит 100 единиц."
  },

  sewing_kit: {
    id: "sewing_kit",
    name: "Набор для шитья",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/sewing-kit.jpg",
    qtyNote: "Нужен полный набор — 100 единиц.",
    description: "Швейный набор. В рецепт идёт целиком.",
    where:
      "Жилые дома — спальни и шкафы, магазины одежды, школы, офисы, иногда больницы. Нужен полный набор на 100 единиц, обноски не подойдут."
  },

  rags: {
    id: "rags",
    name: "Тряпки",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/rags.svg",
    craftable: true,
    description: "Базовый материал. 6 тряпок = 1 верёвка.",
    where:
      "Разрежьте любую одежду ножом в руках. Футболки, рубашки, куртки, штаны — всё подходит. Одежда лежит в домах, на трупах заражённых и в магазинах.",
    recipe: [{ id: "clothes", qty: 1 }],
    tools: [{ id: "knife", qty: 1 }]
  },

  clothes: {
    id: "clothes",
    name: "Одежда",
    category: "material",
    categoryLabel: "Материал",
    image: "img/items/clothes.svg",
    description: "Любая тканевая одежда. Режется на тряпки.",
    where:
      "Дома, шкафы, сушилки, магазины одежды, школы, палатки, трупы заражённых. Для тряпок сгодится почти любой предмет одежды."
  },

  knife: {
    id: "knife",
    name: "Нож",
    category: "tool",
    categoryLabel: "Инструмент",
    image: "img/items/knife.svg",
    tool: true,
    description: "Не расходуется. Нужен, чтобы резать одежду на тряпки.",
    where:
      "Кухни, сараи, охотничьи домики, гаражи, иногда заражённые. Подойдёт кухонный, охотничий, боевой нож или топор — любой режущий инструмент в руках."
  }
};

GZ.CRAFTABLE = ["vest_6b45"];

GZ.PRICES = [];
