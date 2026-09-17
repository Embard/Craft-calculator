window.GZ = window.GZ || {};

/* Fallback only when generated.js is empty. With server catalog these are unused. */
GZ.SEED_ITEMS = {};
GZ.SEED_CRAFTABLE = [];
GZ.SEED_PRICES = [];
GZ.SEED_STATUS = {
  generatedAt: "",
  items: 0,
  craftable: 0,
  prices: 0,
  lootRows: 0,
  icons: 0,
  missing: ["Положите файлы сервера в incoming и запустите tools\\собрать.bat"],
  fromServer: false
};
