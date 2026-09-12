import { Link } from "react-router-dom";
import { production } from "../data/production";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { ArrowUpRight, Bolt, Factory, Spark } from "../components/ui/Icons";
import { Btn } from "../components/ui/bits";
import { useUI } from "../lib/store";

export default function Production() {
  usePageMeta("Производство под заказ — от дизайна до установки | SM-Production", "Полный цикл производства рекламного оборудования: световые вывески, короба, объёмные буквы, стойки ресепшн, ростовые фигуры, кубы.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="Производство" title={<>Мы превращаем идеи <span className="text-accent">в рекламные носители</span></>} text="Собственная производственная база и многолетний опыт: не просто изготовление, а комплексные решения — от концепции до установки и обслуживания.">
        <div className="mt-8 flex flex-wrap gap-4">
          <Btn onClick={() => openLead("Производство под заказ")}>Запрос на сотрудничество</Btn>
          <Btn to="/materialy" variant="ghost">Материалы и технологии</Btn>
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="mb-12 grid gap-4 md:grid-cols-3">
          {[
            [<Factory key="f" size={20} />, "Собственное производство", "Москва и Санкт-Петербург, 750 м²"],
            [<Bolt key="b" size={20} />, "Быстрые сроки", "Изготовление от 3 часов"],
            [<Spark key="s" size={20} />, "Индивидуальный подход", "Личный менеджер на проекте"],
          ].map(([icon, t, d], i) => (
            <Reveal key={t} delay={i * 0.07}>
              <div className="flex items-center gap-4 rounded-2xl border border-line bg-card p-5">
                <span className="rounded-2xl bg-accent/12 p-3 text-accent">{icon}</span>
                <div><p className="font-display text-sm font-bold">{t}</p><p className="text-xs text-mut">{d}</p></div>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {production.map((p, i) => (
            <Reveal key={p.slug} delay={(i % 3) * 0.07}>
              <Link to={`/proizvodstvo/${p.slug}`} className="card-hover img-zoom group relative flex min-h-[300px] flex-col justify-end overflow-hidden rounded-3xl border border-line">
                <img src={p.image} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover opacity-70" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />
                <span className="text-outline absolute right-5 top-4 font-display text-5xl font-black">{p.num}</span>
                <div className="relative p-6">
                  <h2 className="display-h text-xl font-bold text-white group-hover:text-acid">{p.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-white/70">{p.short}</p>
                  <span className="mt-4 inline-flex items-center gap-2 font-display text-[11px] uppercase tracking-[0.2em] text-acid">Подробнее <ArrowUpRight size={13} /></span>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
