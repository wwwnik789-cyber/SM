import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { useUI } from "../../lib/store";
import { PHONE, PHONE_HREF } from "../../lib/format";
import { Close, Logo, Menu, Moon, Phone, Search, Sun } from "../ui/Icons";
import { useLockBody } from "../../hooks/usePageMeta";

const servicesMenu = [
  ["Застройка мероприятий", "/uslugi/zastroyka-meropriyatiy"],
  ["Фотозоны на заказ", "/uslugi/fotozony"],
  ["Имиджевые фотозоны", "/uslugi/imidzhevye-fotozony"],
  ["Выставочные стенды", "/uslugi/vystavochnye-stendy"],
  ["Уличные стенды", "/uslugi/ulichnye-stendy"],
  ["Оформление сцен", "/uslugi/oformlenie-stseny"],
  ["Press-Wall", "/uslugi/press-wall"],
  ["Баннеры", "/uslugi/pechat-bannerov"],
];
const companyMenu = [
  ["О компании", "/o-kompanii"],
  ["Команда", "/team"],
  ["Сотрудничество (B2B)", "/b2b"],
  ["Материалы", "/materialy"],
  ["Вакансии", "/vakansii"],
  ["Отзывы", "/otzyvy"],
];

function Drop({ label, children }) {
  return (
    <div className="group relative hidden lg:block">
      <button className="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-mut transition-colors hover:text-ink">
        {label}
        <svg width="10" height="10" viewBox="0 0 10 10" className="transition-transform duration-300 group-hover:rotate-180"><path d="M1 3l4 4 4-4" stroke="currentColor" strokeWidth="1.6" fill="none" /></svg>
      </button>
      <div className="invisible absolute left-1/2 top-full z-50 -translate-x-1/2 pt-3 opacity-0 transition-all duration-300 group-hover:visible group-hover:opacity-100">
        <div className="glass min-w-[300px] rounded-2xl border border-line p-3 shadow-2xl shadow-black/40">{children}</div>
      </div>
    </div>
  );
}

const DropLink = ({ to, children }) => (
  <Link to={to} className="block rounded-xl px-4 py-2.5 text-sm font-medium text-mut transition-colors hover:bg-accent/10 hover:text-accent">
    {children}
  </Link>
);

export default function Header() {
  const { theme, toggleTheme, openLead, setPaletteOpen } = useUI();
  const [scrolled, setScrolled] = useState(false);
  const [menu, setMenu] = useState(false);
  const loc = useLocation();
  useLockBody(menu);

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  useEffect(() => setMenu(false), [loc.pathname]);

  const nav = "px-3 py-2 text-sm font-semibold text-mut transition-colors hover:text-ink";

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 px-3 md:px-6">
        <div
          className={`mx-auto mt-3 flex max-w-7xl items-center justify-between gap-3 rounded-2xl border px-4 py-3 transition-all duration-500 md:px-6 ${
            scrolled ? "glass border-line shadow-xl shadow-black/25" : "border-transparent"
          }`}
        >
          <Link to="/" className="flex items-center gap-3 text-ink" aria-label="SM-Production — на главную">
            <Logo size={38} />
            <span className="font-display text-sm font-bold tracking-[0.08em]">
              SM<span className="text-accent">•</span>PRODUCTION
            </span>
          </Link>

          <nav className="hidden items-center lg:flex" aria-label="Основная навигация">
            <Drop label="Услуги">
              <div className="grid w-[540px] grid-cols-2 gap-1">
                {servicesMenu.map(([t, to]) => (
                  <DropLink key={to} to={to}>{t}</DropLink>
                ))}
              </div>
              <div className="mt-2 border-t border-line pt-2">
                <DropLink to="/uslugi">→ Все услуги</DropLink>
                <DropLink to="/kalkulyator">→ Калькулятор стоимости</DropLink>
              </div>
            </Drop>
            <Drop label="Производство">
              <DropLink to="/proizvodstvo">Производство под заказ</DropLink>
              <DropLink to="/proizvodstvo/svetovye-vyveski">Световые вывески</DropLink>
              <DropLink to="/proizvodstvo/obemnye-bukvy">Объёмные буквы</DropLink>
              <DropLink to="/materialy">Материалы</DropLink>
            </Drop>
            <NavLink to="/portfolio" className={({ isActive }) => `${nav} ${isActive ? "text-ink" : ""}`}>Портфолио</NavLink>
            <Drop label="Компания">
              {companyMenu.map(([t, to]) => (
                <DropLink key={to} to={to}>{t}</DropLink>
              ))}
            </Drop>
            <NavLink to="/blog" className={({ isActive }) => `${nav} ${isActive ? "text-ink" : ""}`}>Блог</NavLink>
            <NavLink to="/kontakty" className={({ isActive }) => `${nav} ${isActive ? "text-ink" : ""}`}>Контакты</NavLink>
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPaletteOpen(true)}
              className="hidden items-center gap-2 rounded-xl border border-line px-3 py-2 text-sm text-mut transition-colors hover:border-ink hover:text-ink md:flex"
              aria-label="Поиск по сайту"
            >
              <Search size={15} />
              <span className="text-xs">Поиск</span>
              <kbd className="rounded bg-line px-1.5 py-0.5 text-[10px] font-bold">⌘K</kbd>
            </button>
            <button
              onClick={toggleTheme}
              className="rounded-xl border border-line p-2.5 text-mut transition-all hover:rotate-12 hover:border-ink hover:text-ink"
              aria-label="Переключить тему"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <a href={PHONE_HREF} className="hidden items-center gap-2 rounded-xl border border-line px-4 py-2.5 text-sm font-bold transition-colors hover:border-accent hover:text-accent xl:flex">
              <Phone size={15} /> {PHONE}
            </a>
            <button
              onClick={() => openLead()}
              className="btn-sheen hidden rounded-xl bg-accent px-5 py-2.5 font-display text-xs uppercase tracking-[0.14em] text-white sm:block"
            >
              Заявка
            </button>
            <button onClick={() => setMenu(true)} className="rounded-xl border border-line p-2.5 lg:hidden" aria-label="Открыть меню">
              <Menu size={18} />
            </button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {menu && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-bg"
          >
            <div className="flex items-center justify-between px-5 py-5">
              <span className="font-display text-sm font-bold">SM<span className="text-accent">•</span>PRODUCTION</span>
              <button onClick={() => setMenu(false)} className="rounded-xl border border-line p-2.5" aria-label="Закрыть меню">
                <Close size={18} />
              </button>
            </div>
            <nav className="scroll-auto flex h-[calc(100%-80px)] flex-col gap-1 overflow-y-auto px-5 pb-10 pt-4" aria-label="Мобильная навигация">
              {[
                ["Главная", "/"],
                ["Услуги", "/uslugi"],
                ["Калькулятор", "/kalkulyator"],
                ["Производство", "/proizvodstvo"],
                ["Портфолио", "/portfolio"],
                ["Процессы", "/process"],
                ["Аренда", "/arenda"],
                ["SM-Media", "/media"],
                ["Сотрудничество", "/b2b"],
                ["Блог", "/blog"],
                ["Отзывы", "/otzyvy"],
                ["FAQ", "/faq"],
                ["Контакты", "/kontakty"],
              ].map(([t, to], i) => (
                <motion.div key={to} initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 + i * 0.04 }}>
                  <Link to={to} onClick={() => setMenu(false)} className="block border-b border-line py-3 font-display text-2xl font-bold hover:text-accent">
                    {t}
                  </Link>
                </motion.div>
              ))}
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }} className="mt-6 flex flex-col gap-3">
                <a href={PHONE_HREF} className="font-display text-lg text-accent">{PHONE}</a>
                <button onClick={() => { setMenu(false); openLead(); }} className="btn-sheen rounded-xl bg-accent px-6 py-4 font-display text-sm uppercase tracking-widest text-white">
                  Оставить заявку
                </button>
              </motion.div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
