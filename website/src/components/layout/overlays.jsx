import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { useUI } from "../../lib/store";
import { searchSite } from "../../lib/search";
import { useLockBody } from "../../hooks/usePageMeta";
import { ArrowRight, Check, Close, Search, Spark } from "../ui/Icons";
import { Btn } from "../ui/bits";

/* ---------------- Заявка (multi-step lead form) ---------------- */
const TOPICS = ["Фотозона", "Стенд", "Сцена / каше", "Баннеры / печать", "Световая вывеска", "Аренда", "Другое"];
const BUDGETS = ["до 100 тыс ₽", "100–300 тыс ₽", "300 тыс – 1 млн ₽", "1 млн+ ₽", "Пока не знаю"];

export function LeadModal() {
  const { leadOpen, setLeadOpen, leadTopic, notify } = useUI();
  const [step, setStep] = useState(0);
  const [topic, setTopic] = useState("");
  const [date, setDate] = useState("");
  const [budget, setBudget] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);
  useLockBody(leadOpen);

  useEffect(() => {
    if (leadOpen) {
      setStep(0);
      setDone(false);
      setErr("");
      if (leadTopic) setTopic(leadTopic);
    }
  }, [leadOpen, leadTopic]);

  const next = () => {
    if (step === 0 && !topic) return setErr("Выберите, что нужно сделать");
    if (step === 2) {
      if (name.trim().length < 2) return setErr("Представьтесь, пожалуйста");
      if (phone.replace(/\D/g, "").length < 10) return setErr("Проверьте номер телефона");
      const leads = JSON.parse(localStorage.getItem("sm-leads") || "[]");
      leads.push({ topic, date, budget, name, phone, at: new Date().toISOString() });
      localStorage.setItem("sm-leads", JSON.stringify(leads));
      setDone(true);
      notify("Заявка отправлена — свяжемся в течение 15 минут");
      return;
    }
    setErr("");
    setStep(step + 1);
  };

  const input = "w-full rounded-xl border border-line bg-bg2 px-4 py-3.5 text-ink outline-none transition-colors focus:border-accent";

  return (
    <AnimatePresence>
      {leadOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[85] flex items-end justify-center bg-black/60 p-4 backdrop-blur-sm sm:items-center" onClick={() => setLeadOpen(false)}>
          <motion.div
            initial={{ opacity: 0, y: 48, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 300, damping: 28 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-3xl border border-line bg-card p-7 md:p-9"
            role="dialog"
            aria-modal="true"
            aria-label="Оставить заявку"
          >
            {done ? (
              <div className="py-8 text-center">
                <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 260, damping: 16 }} className="inline-block rounded-full bg-acid p-4 text-black">
                  <Check size={26} />
                </motion.span>
                <h3 className="display-h mt-6 text-2xl font-bold">Заявка улетела!</h3>
                <p className="mt-3 text-mut">Личный руководитель проектов свяжется с вами в течение 15 минут в рабочее время. Мы на связи 24/7.</p>
                <Btn onClick={() => setLeadOpen(false)} className="mt-7">Отлично</Btn>
              </div>
            ) : (
              <>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-display text-[10px] uppercase tracking-[0.3em] text-accent">Шаг {step + 1} / 3</p>
                    <h3 className="display-h mt-2 text-xl font-bold md:text-2xl">
                      {step === 0 ? "Что будем делать?" : step === 1 ? "Пара деталей" : "Как с вами связаться?"}
                    </h3>
                  </div>
                  <button onClick={() => setLeadOpen(false)} aria-label="Закрыть" className="rounded-xl border border-line p-2 text-mut hover:text-ink"><Close size={16} /></button>
                </div>

                <div className="mt-4 h-1 overflow-hidden rounded bg-line">
                  <motion.div animate={{ width: `${((step + 1) / 3) * 100}%` }} className="h-full bg-accent" />
                </div>

                <div className="mt-6 min-h-[160px]">
                  {step === 0 && (
                    <div className="flex flex-wrap gap-2">
                      {TOPICS.map((t) => (
                        <button key={t} onClick={() => { setTopic(t); setErr(""); }} className={`rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all ${topic === t ? "border-accent bg-accent text-white" : "border-line text-mut hover:border-ink hover:text-ink"}`}>
                          {t}
                        </button>
                      ))}
                    </div>
                  )}
                  {step === 1 && (
                    <div className="space-y-4">
                      <label className="block">
                        <span className="mb-2 block text-sm font-semibold text-mut">Дата мероприятия (если известна)</span>
                        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className={input} />
                      </label>
                      <div>
                        <span className="mb-2 block text-sm font-semibold text-mut">Ориентир бюджета</span>
                        <div className="flex flex-wrap gap-2">
                          {BUDGETS.map((b) => (
                            <button key={b} onClick={() => setBudget(b)} className={`rounded-xl border px-3.5 py-2 text-sm font-semibold transition-all ${budget === b ? "border-accent bg-accent text-white" : "border-line text-mut hover:border-ink hover:text-ink"}`}>
                              {b}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  {step === 2 && (
                    <div className="space-y-4">
                      <input placeholder="Ваше имя" value={name} onChange={(e) => setName(e.target.value)} className={input} />
                      <input placeholder="+7 ___ ___-__-__" value={phone} onChange={(e) => setPhone(e.target.value)} className={input} inputMode="tel" />
                      <p className="text-xs text-mut">Нажимая кнопку, вы соглашаетесь с <span className="underline">политикой конфиденциальности</span>.</p>
                    </div>
                  )}
                </div>

                {err && <p className="mt-3 text-sm font-semibold text-accent">{err}</p>}

                <div className="mt-6 flex gap-3">
                  {step > 0 && (
                    <button onClick={() => setStep(step - 1)} className="rounded-xl border border-line px-6 py-3.5 font-display text-xs uppercase tracking-widest text-mut hover:text-ink">
                      Назад
                    </button>
                  )}
                  <Btn onClick={next} className="flex-1">
                    {step === 2 ? "Отправить заявку" : "Далее"} <ArrowRight size={15} />
                  </Btn>
                </div>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ---------------- Командная палитра (⌘K) ---------------- */
export function CommandPalette() {
  const { paletteOpen, setPaletteOpen } = useUI();
  const [q, setQ] = useState("");
  const [i, setI] = useState(0);
  const nav = useNavigate();
  const inputRef = useRef(null);
  const results = useMemo(() => searchSite(q), [q]);
  useLockBody(paletteOpen);

  useEffect(() => {
    if (paletteOpen) {
      setQ("");
      setI(0);
      setTimeout(() => inputRef.current?.focus(), 60);
    }
  }, [paletteOpen]);

  const go = (url) => {
    setPaletteOpen(false);
    nav(url);
  };

  return (
    <AnimatePresence>
      {paletteOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[88] bg-black/60 p-4 backdrop-blur-sm" onClick={() => setPaletteOpen(false)}>
          <motion.div
            initial={{ opacity: 0, y: -18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12 }}
            onClick={(e) => e.stopPropagation()}
            className="mx-auto mt-[10vh] w-full max-w-xl overflow-hidden rounded-3xl border border-line bg-card shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="Поиск по сайту"
          >
            <div className="flex items-center gap-3 border-b border-line px-5 py-4">
              <Search size={18} className="text-mut" />
              <input
                ref={inputRef}
                value={q}
                onChange={(e) => { setQ(e.target.value); setI(0); }}
                onKeyDown={(e) => {
                  if (e.key === "ArrowDown") { e.preventDefault(); setI((x) => Math.min(x + 1, results.length - 1)); }
                  if (e.key === "ArrowUp") { e.preventDefault(); setI((x) => Math.max(x - 1, 0)); }
                  if (e.key === "Enter" && results[i]) go(results[i].url);
                }}
                placeholder="Услуги, кейсы, статьи, страницы…"
                className="w-full bg-transparent text-ink outline-none placeholder:text-mut"
              />
              <kbd className="rounded bg-line px-2 py-1 text-[10px] font-bold text-mut">ESC</kbd>
            </div>
            <div className="max-h-[46vh] overflow-y-auto p-2">
              {q.trim() === "" ? (
                <div className="p-4 text-sm text-mut">
                  <p className="mb-3 flex items-center gap-2 font-display text-xs uppercase tracking-[0.2em]"><Spark size={14} className="text-acid" /> Быстрые ссылки</p>
                  {[["Калькулятор стоимости", "/kalkulyator"], ["Смотреть портфолио", "/portfolio"], ["Акция на фотозоны", "/uslugi/akciya-fotozona"], ["Тренды оформления 2026", "/blog/trendy-oformleniya-meropriyatiy-2026"]].map(([t, to]) => (
                    <button key={to} onClick={() => go(to)} className="block w-full rounded-xl px-4 py-2.5 text-left font-medium hover:bg-accent/10 hover:text-accent">
                      {t}
                    </button>
                  ))}
                </div>
              ) : results.length === 0 ? (
                <p className="p-6 text-center text-sm text-mut">Ничего не нашли по «{q}». Попробуйте «фотозона» или «стенд».</p>
              ) : (
                results.map((r, idx) => (
                  <button
                    key={r.url + r.title}
                    onMouseEnter={() => setI(idx)}
                    onClick={() => go(r.url)}
                    className={`flex w-full items-center justify-between gap-3 rounded-xl px-4 py-3 text-left ${idx === i ? "bg-accent/10 text-accent" : ""}`}
                  >
                    <span>
                      <span className="block text-sm font-semibold">{r.title}</span>
                      {r.hint && <span className="mt-0.5 block truncate text-xs text-mut">{r.hint}</span>}
                    </span>
                    <span className="shrink-0 rounded-full border border-line px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-mut">{r.type}</span>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
