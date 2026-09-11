import { Link } from "react-router-dom";
import { EMAIL, PHONE, PHONE_HREF, TG } from "../../lib/format";
import { useUI } from "../../lib/store";
import { Logo, Mail, MapPin, Phone, Send } from "../ui/Icons";

const cols = [
  {
    h: "Услуги",
    links: [
      ["Застройка мероприятий", "/uslugi/zastroyka-meropriyatiy"],
      ["Фотозоны", "/uslugi/fotozony"],
      ["Выставочные стенды", "/uslugi/vystavochnye-stendy"],
      ["Уличные стенды", "/uslugi/ulichnye-stendy"],
      ["Оформление сцен", "/uslugi/oformlenie-stseny"],
      ["Печать баннеров", "/uslugi/pechat-bannerov"],
      ["Все услуги →", "/uslugi"],
    ],
  },
  {
    h: "Компания",
    links: [
      ["О компании", "/o-kompanii"],
      ["Команда", "/team"],
      ["Процессы работы", "/process"],
      ["Сотрудничество", "/b2b"],
      ["Вакансии", "/vakansii"],
      ["Отзывы", "/otzyvy"],
      ["Блог", "/blog"],
    ],
  },
  {
    h: "Инструменты",
    links: [
      ["Калькулятор стоимости", "/kalkulyator"],
      ["Портфолио", "/portfolio"],
      ["Аренда оборудования", "/arenda"],
      ["SM-Media", "/media"],
      ["Энциклопедия материалов", "/materialy"],
      ["Вопросы и ответы", "/faq"],
      ["Карта сайта", "/karta-sayta"],
    ],
  },
];

export default function Footer() {
  const { openLead } = useUI();
  return (
    <footer className="relative mt-28 border-t border-line bg-bg2">
      {/* CTA band */}
      <div className="mx-auto max-w-7xl px-5 py-16 md:py-20">
        <div className="flex flex-col items-start justify-between gap-8 rounded-3xl border border-line bg-card p-8 md:flex-row md:items-center md:p-12">
          <div>
            <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">Готовы начать?</p>
            <h3 className="display-h mt-3 text-2xl font-bold md:text-4xl">Узнайте стоимость вашего проекта за 1 минуту</h3>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => openLead()} className="btn-sheen rounded-xl bg-accent px-7 py-4 font-display text-sm uppercase tracking-[0.14em] text-white">
              Получить расчёт
            </button>
            <Link to="/kalkulyator" className="rounded-xl border border-line px-7 py-4 font-display text-sm uppercase tracking-[0.14em] hover:border-accent hover:text-accent">
              Калькулятор
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-7xl gap-12 px-5 pb-14 md:grid-cols-[1.2fr_1fr_1fr_1fr]">
        <div>
          <Link to="/" className="flex items-center gap-3 text-ink">
            <Logo size={42} />
            <span className="font-display text-sm font-bold tracking-[0.08em]">SM<span className="text-accent">•</span>PRODUCTION</span>
          </Link>
          <p className="mt-5 max-w-xs text-sm leading-relaxed text-mut">
            Производство полного цикла: оформление и застройка мероприятий, световые конструкции и видеопроизводство. Москва и Санкт-Петербург.
          </p>
          <div className="mt-6 flex gap-2">
            <a href={TG} target="_blank" rel="noreferrer" aria-label="Telegram" className="rounded-xl border border-line p-3 text-mut transition-colors hover:border-accent hover:text-accent"><Send size={16} /></a>
            <a href={`mailto:${EMAIL}`} aria-label="Почта" className="rounded-xl border border-line p-3 text-mut transition-colors hover:border-accent hover:text-accent"><Mail size={16} /></a>
            <a href={PHONE_HREF} aria-label="Телефон" className="rounded-xl border border-line p-3 text-mut transition-colors hover:border-accent hover:text-accent"><Phone size={16} /></a>
          </div>
        </div>

        {cols.map((c) => (
          <nav key={c.h} aria-label={c.h}>
            <h4 className="font-display text-xs uppercase tracking-[0.28em] text-mut">{c.h}</h4>
            <ul className="mt-5 space-y-2.5">
              {c.links.map(([t, to]) => (
                <li key={to + t}>
                  <Link to={to} className="link-underline text-sm font-medium text-ink/80 hover:text-ink">{t}</Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="mx-auto grid max-w-7xl gap-4 border-t border-line px-5 py-8 text-sm text-mut md:grid-cols-3">
        <p className="flex items-center gap-2"><MapPin size={14} /> Москва, Остаповский проезд, 9 с13</p>
        <p className="flex items-center gap-2 md:justify-center"><MapPin size={14} /> СПб, ул. Швецова, 41 лит. А</p>
        <p className="md:text-right">Работаем 24/7 · {PHONE}</p>
      </div>

      <div className="overflow-hidden border-t border-line py-6" aria-hidden="true">
        <p className="text-outline display-h whitespace-nowrap text-center text-[11vw] font-black leading-none opacity-40">
          SM-PRODUCTION
        </p>
      </div>

      <div className="border-t border-line px-5 py-5 text-center text-xs text-mut">
        © 2026 SM-Production · <Link to="/politika-konfidencialnosti" className="hover:text-ink">Политика конфиденциальности</Link> · сделано на React + Vite, тренды 2026
      </div>
    </footer>
  );
}
