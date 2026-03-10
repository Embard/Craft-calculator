window.CRAFT_DATA = {
  categories: [
    {
      id: 'containers',
      name: 'Контейнеры',
      icon: '☢',
      items: [
        {
          id: 'container-2',
          name: 'Контейнер 2 слота',
          thumbLabel: 'C2',
          recipe: [
            { name: 'Контейнер 1 слот', qty: 1, thumbLabel: 'C1' },
            { name: 'Сырая резина', qty: 20, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 100, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 10, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-3',
          name: 'Контейнер 3 артефакта',
          thumbLabel: 'C3',
          recipe: [
            { name: 'Контейнер 2 слота', qty: 1, thumbLabel: 'C2' },
            { name: 'Сырая резина', qty: 30, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 150, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 15, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-4',
          name: 'Контейнер 4 артефакта',
          thumbLabel: 'C4',
          recipe: [
            { name: 'Контейнер 3 артефакта', qty: 1, thumbLabel: 'C3' },
            { name: 'Сырая резина', qty: 50, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 200, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 20, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-5',
          name: 'Контейнер 5 артефактов',
          thumbLabel: 'C5',
          recipe: [
            { name: 'Контейнер 4 артефакта', qty: 1, thumbLabel: 'C4' },
            { name: 'Сырая резина', qty: 70, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 300, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 30, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-6',
          name: 'Контейнер 6 артефактов',
          thumbLabel: 'C6',
          recipe: [
            { name: 'Контейнер 5 артефактов', qty: 1, thumbLabel: 'C5' },
            { name: 'Сырая резина', qty: 100, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 400, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 40, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-7',
          name: 'Контейнер 7 артефактов',
          thumbLabel: 'C7',
          recipe: [
            { name: 'Контейнер 6 артефактов', qty: 1, thumbLabel: 'C6' },
            { name: 'Сырая резина', qty: 150, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 500, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 50, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-8',
          name: 'Контейнер 8 слотов',
          thumbLabel: 'C8',
          recipe: [
            { name: 'Контейнер 7 артефактов', qty: 1, thumbLabel: 'C7' },
            { name: 'Сырая резина', qty: 200, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 600, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 70, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-9',
          name: 'Контейнер 9 артефактов',
          thumbLabel: 'C9',
          recipe: [
            { name: 'Контейнер 8 слотов', qty: 1, thumbLabel: 'C8' },
            { name: 'Сырая резина', qty: 300, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 800, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 200, thumbLabel: 'ПВА' }
          ]
        },
        {
          id: 'container-10',
          name: 'Контейнер 10 артефактов',
          thumbLabel: 'C10',
          recipe: [
            { name: 'Контейнер 9 артефактов', qty: 1, thumbLabel: 'C9' },
            { name: 'Сырая резина', qty: 400, thumbLabel: 'РЗ' },
            { name: 'Набор инструментов для тонкой работы', qty: 900, thumbLabel: 'ИН' },
            { name: 'Клей ПВА', qty: 300, thumbLabel: 'ПВА' }
          ]
        }
      ]
    },
    {
      id: 'electronics',
      name: 'Электроника',
      icon: '⚡',
      items: [
        {
          id: 'battery-9v-x5',
          name: 'Батарея 9В x5',
          thumbLabel: '9V',
          recipe: [
            { name: 'Набор инструментов для тонкой работы', qty: 20, thumbLabel: 'ИН' },
            { name: 'Пучок проводов', qty: 1, thumbLabel: 'ПР' },
            { name: 'WD-40', qty: 20, thumbLabel: 'WD' },
            { name: 'Батарея 9В', qty: 6, thumbLabel: '9V' }
          ]
        }
      ]
    },
    {
      id: 'weapons',
      name: 'Оружие',
      icon: '🔫',
      items: [
        {
          id: 'mps-auto-assault-12',
          name: 'MPS Auto Assault-12',
          image: 'assets/mps-auto-assault-12.png',
          thumbLabel: 'MPS',
          recipe: [
            { name: 'USAS-12', qty: 1, image: 'assets/usas-12.png', thumbLabel: 'USA' },
            { name: 'Старый магнит', qty: 2, image: 'assets/old-magnet.png', thumbLabel: 'МАГ' },
            { name: 'Конденсаторы', qty: 100, image: 'assets/capacitors.png', thumbLabel: 'КНД' },
            { name: 'Медная катушка', qty: 100, image: 'assets/copper-coil.png', thumbLabel: 'МК' }
          ]
        },
        {
          id: 'benelli-m4-super-90-12k',
          name: 'Ружье Benelli M4 Super 90 12к',
          image: 'assets/benelli-m4-super-90-12k.png',
          thumbLabel: 'BM4',
          recipe: [
            { name: 'Ружье Benelli M3 Super 90 12к', qty: 1, image: 'assets/benelli-m3-super-90-12k.png', thumbLabel: 'BM3' },
            { name: 'Пучок проводов', qty: 1, image: 'assets/wire-bundle.png', thumbLabel: 'ПР' },
            { name: 'Конденсаторы', qty: 50, image: 'assets/capacitors.png', thumbLabel: 'КНД' },
            { name: 'Медная катушка', qty: 50, image: 'assets/copper-coil.png', thumbLabel: 'МК' }
          ]
        },
        {
          id: 'homemade-rifle',
          name: 'Самодельный автомат',
          image: 'assets/homemade-rifle.png',
          thumbLabel: 'СА',
          recipe: [
            { name: 'Изолента', qty: 10, image: 'assets/duct-tape.png', thumbLabel: 'ИЗО' },
            { name: 'Предохранители', qty: 5, image: 'assets/fuses.png', thumbLabel: 'ПРД' },
            { name: 'Ржавые гайки', qty: 5, image: 'assets/rusty-nuts.png', thumbLabel: 'РГ' },
            { name: 'Набор инструментов для черновых работ', qty: 10, image: 'assets/rough-tools.png', thumbLabel: 'НИЧ' }
          ]
        },
        {
          id: 'pp-19-vityaz-9x19',
          name: 'ПП-19-01 Витязь 9x19',
          image: 'assets/pp-19-vityaz-9x19.png',
          thumbLabel: 'ПП19',
          recipe: [
            { name: 'АПС 9x18ПМ', qty: 1, image: 'assets/aps-9x18pm.png', thumbLabel: 'АПС' },
            { name: 'Двусторонняя печатная плата FP1', qty: 10, image: 'assets/fp1-board.png', thumbLabel: 'FP1' },
            { name: 'Гайка шестигранная оцинкованная', qty: 10, image: 'assets/hex-nut-galvanized.png', thumbLabel: 'ГШО' },
            { name: 'Инструменты калибровки', qty: 3000, image: 'assets/calibration-tools.png', thumbLabel: 'ИК' },
            { name: 'Предохранители', qty: 800, image: 'assets/fuses-bulk.png', thumbLabel: 'ПРД' },
            { name: 'Ржавые гайки', qty: 1000, image: 'assets/rusty-nuts-bulk.png', thumbLabel: 'РГ' },
            { name: 'Медная катушка', qty: 1600, image: 'assets/copper-coil-bulk.png', thumbLabel: 'МК' },
            { name: 'Ржавые болты', qty: 1000, image: 'assets/rusty-bolts.png', thumbLabel: 'РБ' }
          ]
        },
        {
          id: 'aps-9x18pm',
          name: 'АПС 9x18ПМ',
          image: 'assets/aps-9x18pm-top.png',
          thumbLabel: 'АПС',
          recipe: [
            { name: 'МР-443 Грач 9x19', qty: 1, image: 'assets/mp-443-grach-9x19.png', thumbLabel: 'МР' },
            { name: 'Двусторонняя печатная плата FP1', qty: 5, image: 'assets/fp1-board.png', thumbLabel: 'FP1' },
            { name: 'Гайка шестигранная оцинкованная', qty: 5, image: 'assets/hex-nut-galvanized.png', thumbLabel: 'ГШО' },
            { name: 'Инструменты калибровки', qty: 1500, image: 'assets/calibration-tools.png', thumbLabel: 'ИК' },
            { name: 'Предохранители', qty: 500, image: 'assets/fuses-bulk.png', thumbLabel: 'ПРД' },
            { name: 'Ржавые гайки', qty: 500, image: 'assets/rusty-nuts-bulk.png', thumbLabel: 'РГ' },
            { name: 'Медная катушка', qty: 800, image: 'assets/copper-coil-aps.png', thumbLabel: 'МК' },
            { name: 'Ржавые болты', qty: 500, image: 'assets/rusty-bolts-aps.png', thumbLabel: 'РБ' }
          ]
        }
      ]
    },
    {
      id: 'quests',
      name: 'Квесты',
      icon: '🧭',
      items: []
    },
    {
      id: 'other',
      name: 'Разное',
      icon: '🧰',
      items: []
    }
  ]
};
