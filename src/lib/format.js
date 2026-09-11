export const fmtMoney = (n) =>
  new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(Math.round(n)) + " ₽";

export const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });

export function plural(n, [one, few, many]) {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

export const PHONE = "+7 495 799-00-19";
export const PHONE_HREF = "tel:+74957990019";
export const EMAIL = "sm-pro1@yandex.ru";
export const TG = "https://t.me/sm_production_sm";
