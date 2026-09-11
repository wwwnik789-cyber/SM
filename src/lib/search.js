import { services } from "../data/services";
import { portfolio } from "../data/portfolio";
import { posts } from "../data/blog";
import { production } from "../data/production";
import { materials } from "../data/materials";

const pages = [
  { title: "Главная", url: "/", type: "Страница" },
  { title: "Услуги", url: "/uslugi", type: "Страница" },
  { title: "Производство под заказ", url: "/proizvodstvo", type: "Страница" },
  { title: "Портфолио", url: "/portfolio", type: "Страница" },
  { title: "Процессы работы", url: "/process", type: "Страница" },
  { title: "Калькулятор стоимости", url: "/kalkulyator", type: "Инструмент" },
  { title: "Аренда оборудования", url: "/arenda", type: "Страница" },
  { title: "SM-Media — видеопроизводство", url: "/media", type: "Страница" },
  { title: "Сотрудничество с агентствами", url: "/b2b", type: "Страница" },
  { title: "О компании", url: "/o-kompanii", type: "Страница" },
  { title: "Команда", url: "/team", type: "Страница" },
  { title: "Блог", url: "/blog", type: "Страница" },
  { title: "Отзывы", url: "/otzyvy", type: "Страница" },
  { title: "Вопросы и ответы", url: "/faq", type: "Страница" },
  { title: "Материалы", url: "/materialy", type: "Страница" },
  { title: "Вакансии", url: "/vakansii", type: "Страница" },
  { title: "Контакты", url: "/kontakty", type: "Страница" },
  { title: "Карта сайта", url: "/karta-sayta", type: "Страница" },
];

export const searchIndex = [
  ...pages,
  ...services.map((s) => ({ title: s.title, url: `/uslugi/${s.slug}`, type: "Услуга", hint: s.short })),
  ...production.map((p) => ({ title: p.title, url: `/proizvodstvo/${p.slug}`, type: "Производство", hint: p.short })),
  ...portfolio.map((p) => ({ title: p.title, url: `/portfolio/${p.slug}`, type: "Кейс", hint: p.client })),
  ...posts.map((p) => ({ title: p.title, url: `/blog/${p.slug}`, type: "Блог", hint: p.excerpt })),
  ...materials.map((m) => ({ title: m.name, url: "/materialy", type: "Материал", hint: m.use })),
];

const norm = (s) => (s || "").toLowerCase().replace(/ё/g, "е");

export function searchSite(q) {
  const query = norm(q.trim());
  if (!query) return [];
  return searchIndex
    .filter((e) => norm(e.title).includes(query) || norm(e.hint || "").includes(query) || norm(e.type).includes(query))
    .slice(0, 9);
}
