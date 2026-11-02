// Предварительный расчёт стоимости фотозоны / пресс-волла.
// Тарифы аппроксимируют открытую таблицу стандартных конструкций sm-production.ru.

export const MATERIALS = [
  { id: "banner", label: "Баннер BlackBack на брусе", k: 1 },
  { id: "fabric", label: "Ткань с силиконовым кантом", k: 1.18 },
  { id: "mirror", label: "Зеркальный полистирол + декор", k: 1.4 },
];

export const OPTIONS = [
  { id: "light", label: "Контурная LED-подсветка", price: 18000 },
  { id: "letters", label: "Объёмные буквы (до 10 шт.)", price: 26000 },
  { id: "podium", label: "Подиум с зеркальным полом", price: 21000 },
];

export function calcPhotozone({ w = 300, h = 250, material = "banner", options = [], urgent = false }) {
  const area = (w * h) / 10000; // м²
  const perimeter = (2 * (w + h)) / 100; // м
  const rate = area <= 6 ? 5000 : area <= 10 ? 4600 : 4400;
  const mat = MATERIALS.find((m) => m.id === material) || MATERIALS[0];

  const frame = area * rate + perimeter * 450;
  const base = frame * mat.k;
  const extras = options.reduce((sum, id) => {
    const o = OPTIONS.find((x) => x.id === id);
    return sum + (o ? o.price : 0);
  }, 0);

  let total = base + extras;
  if (urgent) total *= 1.3;

  const r100 = (v) => Math.round(v / 100) * 100;
  return {
    area: +area.toFixed(1),
    frame: r100(frame),
    base: r100(base),
    extras: r100(extras),
    total: r100(total),
  };
}

// Таблица стандартных конструкций (как на исходном сайте)
export const STANDARD_SIZES = [
  { size: "2 × 2 м", label: "Компактный формат", use: "Фотозона, welcome-зона", price: 24900 },
  { size: "2 × 2,5 м", label: "Вертикальный акцент", use: "Пресс-волл, инфозона", price: 29200 },
  { size: "2 × 3 м", label: "Универсальный", use: "Пресс-волл, баннер", price: 32000 },
  { size: "2,5 × 2,5 м", label: "Квадрат", use: "Фотозона", price: 32000 },
  { size: "3 × 2,5 м", label: "Классика", use: "Пресс-волл, бренд-зона", price: 38300 },
  { size: "4 × 2,5 м", label: "Широкий", use: "Презентация", price: 44500 },
  { size: "3 × 3 м", label: "Классика для мероприятий", use: "Фотозона, бренд-зона", price: 44500 },
  { size: "4 × 3 м", label: "Для масштабных событий", use: "Презентация, сцена", price: 53500 },
  { size: "5 × 3 м", label: "Максимальная видимость", use: "Оформление сцены", price: 65800 },
];

export const STREET_STANDS = [
  { size: "9 × 3 × 4 м", price: 400000, note: "Проект «Пятёрочка»" },
  { size: "9 × 3 × 9 м", price: 300000, note: "Магазин МЕРЧА в Лужниках" },
  { size: "10 × 5 × 10 м", price: 600000, note: "CTC Kids на VK Fest" },
];
