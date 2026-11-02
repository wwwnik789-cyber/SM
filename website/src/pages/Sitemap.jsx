import { Link } from "react-router-dom";
import { services } from "../data/services";
import { portfolio } from "../data/portfolio";
import { posts } from "../data/blog";
import { production } from "../data/production";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";

const groups = [
  { h: "Основные", links: [["Главная", "/"], ["Услуги", "/uslugi"], ["Производство", "/proizvodstvo"], ["Портфолио", "/portfolio"], ["Процессы", "/process"], ["Калькулятор", "/kalkulyator"], ["Аренда", "/arenda"], ["SM-Media", "/media"], ["Сотрудничество", "/b2b"]] },
  { h: "Компания", links: [["О компании", "/o-kompanii"], ["Команда", "/team"], ["Вакансии", "/vakansii"], ["Блог", "/blog"], ["Отзывы", "/otzyvy"], ["FAQ", "/faq"], ["Материалы", "/materialy"], ["Контакты", "/kontakty"], ["Политика конфиденциальности", "/politika-konfidencialnosti"]] },
];

export default function Sitemap() {
  usePageMeta("Карта сайта | SM-Production");
  return (
    <>
      <PageHero overline="Навигация" title={<>Карта <span className="text-accent">сайта</span></>} text="Все страницы, услуги, кейсы и статьи — на одном экране." />
      <section className="mx-auto grid max-w-7xl gap-12 px-5 md:grid-cols-2 lg:grid-cols-4">
        {groups.map((g) => (
          <div key={g.h}>
            <h2 className="font-display text-xs uppercase tracking-[0.28em] text-mut">{g.h}</h2>
            <ul className="mt-5 space-y-2.5">
              {g.links.map(([t, to]) => (
                <li key={to}><Link to={to} className="link-underline text-sm font-semibold">{t}</Link></li>
              ))}
            </ul>
          </div>
        ))}
        <div>
          <h2 className="font-display text-xs uppercase tracking-[0.28em] text-mut">Услуги</h2>
          <ul className="mt-5 space-y-2.5">
            {services.map((s) => (
              <li key={s.slug}><Link to={`/uslugi/${s.slug}`} className="link-underline text-sm font-semibold">{s.title}</Link></li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="font-display text-xs uppercase tracking-[0.28em] text-mut">Производство</h2>
          <ul className="mt-5 space-y-2.5">
            {production.map((p) => (
              <li key={p.slug}><Link to={`/proizvodstvo/${p.slug}`} className="link-underline text-sm font-semibold">{p.title}</Link></li>
            ))}
          </ul>
        </div>
        <div className="md:col-span-2 lg:col-span-2">
          <h2 className="font-display text-xs uppercase tracking-[0.28em] text-mut">Кейсы и блог</h2>
          <div className="mt-5 grid gap-x-8 gap-y-2.5 sm:grid-cols-2">
            {[...portfolio.map((p) => [p.title, `/portfolio/${p.slug}`]), ...posts.map((p) => [p.title, `/blog/${p.slug}`])].map(([t, to]) => (
              <Link key={to} to={to} className="link-underline text-sm font-semibold text-mut hover:text-ink">{t}</Link>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
