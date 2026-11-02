import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import { serviceGroups, services } from "../data/services";
import { production } from "../data/production";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { ArrowUpRight, Factory } from "../components/ui/Icons";
import { useUI } from "../lib/store";

function ServiceCard({ service }) {
  return (
    <Link to={`/uslugi/${service.slug}`} className="card-hover img-zoom group flex h-full flex-col overflow-hidden rounded-3xl border border-line bg-card">
      <div className="relative overflow-hidden">
        <img src={service.image} alt={service.title} loading="lazy" className="h-48 w-full object-cover" />
        <span className="absolute right-4 top-4 rounded-full bg-black/60 px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white backdrop-blur">
          Услуга
        </span>
      </div>
      <div className="flex flex-1 flex-col p-6">
        <h3 className="display-h text-xl font-bold group-hover:text-accent">{service.title}</h3>
        <p className="mt-3 flex-1 text-sm leading-relaxed text-mut">{service.short}</p>
        <span className="mt-5 flex items-center justify-between border-t border-line pt-4 font-display text-[11px] uppercase tracking-[0.16em] text-accent">
          Подробнее
          <ArrowUpRight size={17} className="transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
        </span>
      </div>
    </Link>
  );
}

export default function Services() {
  usePageMeta({
    title: "Услуги по оформлению мероприятий | SM Production",
    description: "Все услуги SM Production: застройка мероприятий, фотозоны, выставочные стенды, оформление сцен, рекламное производство, печать и монтаж.",
    path: "/uslugi",
  });
  const { openLead } = useUI();

  return (
    <>
      <PageHero
        overline="Услуги"
        title={<>Все направления <span className="text-accent">в понятной структуре</span></>}
        text="Выберите задачу, а не технологию. Внутри каждого направления — проектирование, производство, логистика и монтаж."
      >
        <nav className="mt-8 flex flex-wrap gap-2" aria-label="Разделы каталога">
          {serviceGroups.map((group) => (
            <a key={group.key} href={`#${group.key}`} className="rounded-full border border-line px-4 py-2 text-xs font-semibold text-mut transition-colors hover:border-accent hover:text-accent">
              {group.title}
            </a>
          ))}
          <a href="#production" className="rounded-full border border-line px-4 py-2 text-xs font-semibold text-mut transition-colors hover:border-accent hover:text-accent">
            Рекламное производство
          </a>
        </nav>
      </PageHero>

      <div className="mx-auto max-w-7xl space-y-24 px-5">
        {serviceGroups.map((group) => {
          const items = services.filter((service) => service.group === group.key);
          return (
            <section key={group.key} id={group.key} className="scroll-mt-32" aria-labelledby={`${group.key}-title`}>
              <div className="mb-8 grid gap-4 border-t border-line pt-7 md:grid-cols-[1fr_1fr] md:items-end">
                <div>
                  <p className="font-display text-[11px] uppercase tracking-[0.25em] text-accent">{String(items.length).padStart(2, "0")} услуг</p>
                  <h2 id={`${group.key}-title`} className="display-h mt-3 text-2xl font-bold md:text-4xl">{group.title}</h2>
                </div>
                <p className="max-w-xl text-sm leading-relaxed text-mut md:justify-self-end">{group.short}</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {items.map((service, index) => (
                  <Reveal key={service.slug} delay={(index % 3) * 0.06}>
                    <ServiceCard service={service} />
                  </Reveal>
                ))}
              </div>
            </section>
          );
        })}

        <section id="production" className="scroll-mt-32" aria-labelledby="production-title">
          <div className="mb-8 grid gap-4 border-t border-line pt-7 md:grid-cols-[1fr_1fr] md:items-end">
            <div>
              <p className="flex items-center gap-2 font-display text-[11px] uppercase tracking-[0.25em] text-accent"><Factory size={15} /> Собственные цеха</p>
              <h2 id="production-title" className="display-h mt-3 text-2xl font-bold md:text-4xl">Рекламное производство</h2>
            </div>
            <p className="max-w-xl text-sm leading-relaxed text-mut md:justify-self-end">Отдельные изделия и постоянные конструкции: вывески, световые короба, объёмные буквы, ресепшн и ростовые фигуры.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {production.map((item, index) => (
              <Reveal key={item.slug} delay={(index % 3) * 0.06}>
                <Link to={`/proizvodstvo/${item.slug}`} className="card-hover group block h-full rounded-3xl border border-line bg-card p-6">
                  <span className="font-display text-xs text-accent">{item.num}</span>
                  <h3 className="display-h mt-4 text-xl font-bold group-hover:text-accent">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-mut">{item.short}</p>
                  <span className="mt-6 inline-flex items-center gap-2 font-display text-[11px] uppercase tracking-[0.16em] text-accent">Подробнее <ArrowUpRight size={14} /></span>
                </Link>
              </Reveal>
            ))}
          </div>
        </section>
      </div>

      <section className="mx-auto max-w-7xl px-5 pb-4 pt-24">
        <div className="flex flex-col items-start justify-between gap-6 rounded-3xl border border-line bg-card p-8 md:flex-row md:items-center md:p-10">
          <div>
            <h2 className="display-h text-2xl font-bold">Не нашли точное название задачи?</h2>
            <p className="mt-2 text-mut">Пришлите бриф или референс — соберём решение из нескольких производственных направлений.</p>
          </div>
          <button onClick={() => openLead("Индивидуальный проект")} className="btn-sheen rounded-xl bg-accent px-7 py-4 font-display text-sm uppercase tracking-[0.14em] text-white">Обсудить проект</button>
        </div>
      </section>
    </>
  );
}
