import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import { serviceCategories, services } from "../data/services";
import PageHero from "../components/ui/PageHero";
import { Chip } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { ArrowUpRight } from "../components/ui/Icons";
import { fmtMoney } from "../lib/format";
import { useUI } from "../lib/store";

export default function Services() {
  usePageMeta("Услуги SM-Production — фотозоны, стенды, сцены, баннеры", "Полный спектр услуг по оформлению и брендированию мероприятий: застройка, фотозоны, стенды, печать, световые конструкции.");
  const [cat, setCat] = useState("Все");
  const { openLead } = useUI();
  const list = useMemo(() => (cat === "Все" ? services : services.filter((s) => s.category === cat)), [cat]);

  return (
    <>
      <PageHero overline="Услуги" title={<>Всё для оформления <span className="text-accent">вашего события</span></>} text="Полный цикл — от разработки концепции до реализации: декорирование, брендирование и монтаж конструкций любого уровня сложности.">
        <div className="mt-8 flex flex-wrap gap-2">
          {serviceCategories.map((c) => (
            <Chip key={c} active={cat === c} onClick={() => setCat(c)}>{c}</Chip>
          ))}
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5 pb-10">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {list.map((s, i) => (
            <Reveal key={s.slug} delay={(i % 3) * 0.06}>
              <Link to={`/uslugi/${s.slug}`} className={`card-hover img-zoom group flex h-full flex-col overflow-hidden rounded-3xl border ${s.accent ? "border-accent" : "border-line"} bg-card`}>
                <div className="relative overflow-hidden">
                  <img src={s.image} alt="" loading="lazy" className="h-48 w-full object-cover" />
                  {s.accent && <span className="absolute left-4 top-4 rounded-full bg-accent px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white">Акция</span>}
                  <span className="absolute right-4 top-4 rounded-full bg-black/50 px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white backdrop-blur">{s.category}</span>
                </div>
                <div className="flex flex-1 flex-col p-6">
                  <h2 className="display-h text-xl font-bold group-hover:text-accent">{s.title}</h2>
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-mut">{s.short}</p>
                  <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
                    <span className="text-sm font-bold text-accent">{s.priceFrom ? `от ${fmtMoney(s.priceFrom)}` : "Расчёт по брифу"}</span>
                    <ArrowUpRight size={17} className="text-mut transition-all group-hover:translate-x-1 group-hover:-translate-y-1 group-hover:text-accent" />
                  </div>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-4 pt-14">
        <div className="flex flex-col items-start justify-between gap-6 rounded-3xl border border-line bg-card p-8 md:flex-row md:items-center md:p-10">
          <div>
            <h2 className="display-h text-2xl font-bold">Не нашли нужную услугу?</h2>
            <p className="mt-2 text-mut">Расскажите о задаче — предложим решение и смету по позициям.</p>
          </div>
          <button onClick={() => openLead("Другое")} className="btn-sheen rounded-xl bg-accent px-7 py-4 font-display text-sm uppercase tracking-[0.14em] text-white">Обсудить задачу</button>
        </div>
      </section>
    </>
  );
}
