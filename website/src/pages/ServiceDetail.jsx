import { Link, useParams } from "react-router-dom";
import { getService, getServiceGroup, services } from "../data/services";
import { SITE_URL, usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Accordion, Btn, ArrowLink } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Check, Clock, MapPin } from "../components/ui/Icons";
import { useUI } from "../lib/store";

export default function ServiceDetail() {
  const { slug } = useParams();
  const s = getService(slug);
  const group = s ? getServiceGroup(s.group) : null;
  const path = `/uslugi/${slug}`;
  const schema = s ? [
    {
      "@type": "Service",
      "@id": `${SITE_URL}${path}#service`,
      name: s.title,
      description: s.seoDescription,
      url: `${SITE_URL}${path}`,
      image: `${SITE_URL}${s.image}`,
      provider: { "@id": `${SITE_URL}/#organization` },
      areaServed: ["Москва", "Московская область", "Россия"],
    },
    {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Главная", item: `${SITE_URL}/` },
        { "@type": "ListItem", position: 2, name: "Услуги", item: `${SITE_URL}/uslugi` },
        { "@type": "ListItem", position: 3, name: s.title, item: `${SITE_URL}${path}` },
      ],
    },
    ...(s.faq ? [{
      "@type": "FAQPage",
      mainEntity: s.faq.map((item) => ({
        "@type": "Question",
        name: item.q,
        acceptedAnswer: { "@type": "Answer", text: item.a },
      })),
    }] : []),
  ] : [];
  usePageMeta({
    title: s?.seoTitle || "Услуга не найдена | SM Production",
    description: s?.seoDescription || "Запрошенная услуга не найдена.",
    path,
    image: s?.image,
    noindex: !s,
    schema,
  });
  const { openLead } = useUI();
  if (!s) return <NotFound />;

  const related = services.filter((item) => item.slug !== s.slug && item.group === s.group).slice(0, 3);

  return (
    <>
      <section className="relative overflow-hidden pt-36 md:pt-44">
        <div className="grid-bg mask-fade-b absolute inset-0 opacity-50" />
        <div className="relative mx-auto max-w-7xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/uslugi" className="hover:text-ink">Услуги</Link> / <span className="text-ink">{s.title}</span>
          </nav>
          <div className="grid items-end gap-10 lg:grid-cols-[1.2fr_1fr]">
            <Reveal>
              <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">{s.eyebrow || group?.title}</p>
              <h1 className="display-h mt-4 text-4xl font-black md:text-6xl">{s.title}</h1>
              <p className="mt-6 max-w-xl text-lg text-mut">{s.short}</p>
              <div className="mt-8 flex flex-wrap gap-4">
                <Btn onClick={() => openLead(s.title)}>{s.primaryCta || "Получить расчёт"}</Btn>
                <Btn to="/kalkulyator" variant="ghost">Рассчитать стоимость</Btn>
              </div>
            </Reveal>
            <Reveal delay={0.15}>
              <div className="img-zoom overflow-hidden rounded-3xl border border-line">
                <img src={s.image} alt={s.title} className="h-72 w-full object-cover lg:h-80" />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr]">
          <Reveal>
            <div className="space-y-5 text-lg leading-relaxed text-ink/85">
              {s.long.map((p, i) => <p key={i}>{p}</p>)}
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="rounded-3xl border border-line bg-card p-7">
              <h2 className="font-display text-sm uppercase tracking-[0.2em] text-mut">Что входит</h2>
              <ul className="mt-5 space-y-3.5">
                {s.features.map((f) => (
                  <li key={f} className="flex items-start gap-3 text-sm font-medium">
                    <span className="mt-0.5 rounded-full bg-acid/15 p-1 text-acid"><Check size={12} /></span>{f}
                  </li>
                ))}
              </ul>
              <div className="mt-6 space-y-2 border-t border-line pt-5 text-sm text-mut">
                <p className="flex items-start gap-2"><Clock size={14} className="mt-0.5 shrink-0 text-accent" /> {s.leadTime}</p>
                <p className="flex items-start gap-2"><MapPin size={14} className="mt-0.5 shrink-0 text-accent" /> Москва и Московская область, выездные проекты по России</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {s.gallery?.length > 0 && (
        <section className="mx-auto max-w-7xl px-5 pb-20" aria-labelledby="service-gallery-title">
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Применение</p>
            <h2 id="service-gallery-title" className="display-h mt-3 text-3xl font-bold md:text-5xl">Что можно изготовить</h2>
          </Reveal>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {s.gallery.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.07}>
                <figure className="img-zoom h-full overflow-hidden rounded-3xl border border-line bg-card">
                  <div className="overflow-hidden"><img src={item.image} alt={item.alt} loading="lazy" className="h-60 w-full object-cover" /></div>
                  <figcaption className="p-6">
                    <h3 className="font-display text-lg font-bold">{item.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-mut">{item.text}</p>
                  </figcaption>
                </figure>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {s.sections?.length > 0 && (
        <section className="border-y border-line bg-bg2 py-20">
          <div className="mx-auto max-w-7xl px-5">
            <Reveal>
              <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Подробно</p>
              <h2 className="display-h mt-3 text-3xl font-bold md:text-5xl">Материал, печать и дизайн</h2>
            </Reveal>
            <div className="mt-10 grid gap-5 md:grid-cols-2">
              {s.sections.map((section, index) => (
                <Reveal key={section.h} delay={(index % 2) * 0.07}>
                  <article className="img-zoom h-full overflow-hidden rounded-3xl border border-line bg-card">
                    {section.image && (
                      <div className="overflow-hidden">
                        <img src={section.image} alt={section.alt || ""} loading="lazy" className="h-64 w-full object-cover" />
                      </div>
                    )}
                    <div className="p-7 md:p-8">
                      <h3 className="display-h text-xl font-bold">{section.h}</h3>
                      {section.p && <p className="mt-4 leading-relaxed text-mut">{section.p}</p>}
                      {section.list && (
                        <ul className="mt-5 space-y-3">
                          {section.list.map((item) => (
                            <li key={item} className="flex items-start gap-3 text-sm leading-relaxed text-ink/85">
                              <span className="mt-2 h-1.5 w-1.5 shrink-0 rotate-45 bg-accent" />{item}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </article>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      {s.process?.length > 0 && (
        <section className="mx-auto max-w-7xl px-5 py-20" aria-labelledby="service-process-title">
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Процесс</p>
            <h2 id="service-process-title" className="display-h mt-3 text-3xl font-bold md:text-5xl">От идеи до монтажа</h2>
          </Reveal>
          <ol className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {s.process.map((step, index) => (
              <Reveal key={step.title} delay={(index % 3) * 0.06}>
                <li className="img-zoom h-full overflow-hidden rounded-3xl border border-line bg-card">
                  {step.image && (
                    <div className="overflow-hidden">
                      <img src={step.image} alt={step.alt || ""} loading="lazy" className="h-44 w-full object-cover" />
                    </div>
                  )}
                  <div className="p-6">
                    <span className="font-display text-xs text-accent">{String(index + 1).padStart(2, "0")}</span>
                    <h3 className="mt-4 font-display text-lg font-bold">{step.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-mut">{step.text}</p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ol>
        </section>
      )}

      {s.faq?.length > 0 && (
        <section className="mx-auto max-w-4xl px-5 pb-20" aria-labelledby="service-faq-title">
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">FAQ</p>
            <h2 id="service-faq-title" className="display-h mb-8 mt-3 text-3xl font-bold md:text-5xl">Частые вопросы</h2>
          </Reveal>
          <Accordion items={s.faq} />
        </section>
      )}

      {related.length > 0 && (
        <section className="mx-auto max-w-7xl px-5 pb-10">
          <h2 className="display-h mb-8 text-2xl font-bold">Рядом по теме</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {related.map((r) => (
              <Link key={r.slug} to={`/uslugi/${r.slug}`} className="card-hover group rounded-2xl border border-line bg-card p-6">
                <p className="font-display text-base font-bold group-hover:text-accent">{r.title}</p>
                <p className="mt-2 line-clamp-2 text-sm text-mut">{r.short}</p>
              </Link>
            ))}
          </div>
          <div className="mt-10"><ArrowLink to="/uslugi">Все услуги</ArrowLink></div>
        </section>
      )}
    </>
  );
}
