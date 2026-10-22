import { Link, useParams } from "react-router-dom";
import { getRelated, getService } from "../data/services";
import { usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Accordion, Btn, ArrowLink, SectionHead } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Check, Clock, MapPin, Spark } from "../components/ui/Icons";
import { fmtMoney, PHONE, PHONE_HREF, TG } from "../lib/format";
import { useUI } from "../lib/store";

export default function ServiceDetail() {
  const { slug } = useParams();
  const s = getService(slug);
  usePageMeta(s ? `${s.title} — SM-Production` : "Услуга не найдена", s?.short);
  const { openLead } = useUI();
  if (!s) return <NotFound />;

  const related = getRelated(s);

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
              <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">
                {s.category}{s.isNew && <span className="ml-3 rounded-full bg-acid px-2.5 py-1 text-[10px] tracking-widest text-black">Новое</span>}
              </p>
              <h1 className="display-h mt-4 text-4xl font-black md:text-6xl">{s.title}</h1>
              <p className="mt-6 max-w-xl text-lg text-mut">{s.short}</p>
              <div className="mt-8 flex flex-wrap gap-4">
                <Btn onClick={() => openLead(s.title)}>Заказать <span className="opacity-70">{s.priceFrom ? `от ${fmtMoney(s.priceFrom)}` : ""}</span></Btn>
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
                <p className="flex items-center gap-2"><Clock size={14} className="text-accent" /> Производство и монтаж за 24 часа</p>
                <p className="flex items-center gap-2"><MapPin size={14} className="text-accent" /> Москва и МО, выездные бригады по РФ</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {s.bullets && (
        <section className="border-y border-line bg-bg2 py-20">
          <div className="mx-auto max-w-7xl px-5">
            <SectionHead overline="Преимущества" title="Почему это работает" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {s.bullets.map((b, i) => (
                <Reveal key={b.h} delay={(i % 3) * 0.07}>
                  <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                    <span className="inline-flex rounded-2xl bg-accent/12 p-3 text-acid"><Spark size={18} /></span>
                    <h3 className="mt-4 font-display text-base font-bold">{b.h}</h3>
                    {b.p && <p className="mt-2.5 text-sm leading-relaxed text-mut">{b.p}</p>}
                  </div>
                </Reveal>
              ))}
            </div>
            {s.advantages && (
              <ul className="mt-8 grid gap-3 rounded-3xl border border-line bg-card p-7 md:grid-cols-2">
                {s.advantages.map((a) => (
                  <li key={a} className="flex items-start gap-3 text-sm font-medium">
                    <span className="mt-0.5 rounded-full bg-acid/15 p-1 text-acid"><Check size={12} /></span>{a}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}

      {s.table && (
        <section className="mx-auto max-w-7xl px-5 py-20">
          <SectionHead overline="Применение" title={s.table.title} />
          <Reveal>
            <div className="overflow-x-auto rounded-3xl border border-line bg-card">
              <table className="w-full min-w-[640px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-line">
                    {s.table.headers.map((h) => (
                      <th key={h} className="px-6 py-4 font-display text-xs uppercase tracking-[0.18em] text-mut">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {s.table.rows.map((row, i) => (
                    <tr key={i} className="border-b border-line last:border-0">
                      {row.map((cell, j) => (
                        <td key={j} className={`px-6 py-5 align-top text-sm leading-relaxed ${j === 0 ? "font-semibold text-ink" : "text-mut"}`}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Reveal>
        </section>
      )}

      {s.steps && (
        <section className="border-y border-line bg-bg2 py-20">
          <div className="mx-auto max-w-7xl px-5">
            <SectionHead overline="Процесс" title="Как мы работаем" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {s.steps.map(([t, d], i) => (
                <Reveal key={t} delay={(i % 3) * 0.07}>
                  <div className="relative h-full rounded-2xl border border-line bg-card p-6">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent font-display text-sm font-black text-white">{i + 1}</span>
                    <h3 className="mt-4 font-display text-base font-bold">{t}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-mut">{d}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      {s.pricing && (
        <section className="mx-auto max-w-7xl px-5 py-20">
          <SectionHead overline="Цены" title={s.pricing.title} text={s.pricing.note} />
          <Reveal>
            <div className="overflow-x-auto rounded-3xl border border-line bg-card">
              <table className="w-full min-w-[560px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-line">
                    {s.pricing.headers.map((h) => (
                      <th key={h} className="px-6 py-4 font-display text-xs uppercase tracking-[0.18em] text-mut">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {s.pricing.rows.map((row, i) => (
                    <tr key={i} className="border-b border-line last:border-0">
                      {row.map((cell, j) => (
                        <td key={j} className={`px-6 py-4 text-sm ${j === 0 ? "font-semibold text-ink" : "font-bold text-accent"}`}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {s.pricing.foot && <p className="px-6 pb-5 pt-3 text-xs text-mut">{s.pricing.foot}</p>}
            </div>
          </Reveal>
          {s.promo && (
            <Reveal delay={0.1}>
              <p className="mt-6 rounded-2xl border border-accent/40 bg-accent/10 px-6 py-4 text-sm font-semibold text-ink">{s.promo}</p>
            </Reveal>
          )}
        </section>
      )}

      {s.gallery && (
        <section className="border-y border-line bg-bg2 py-20">
          <div className="mx-auto max-w-7xl px-5">
            <SectionHead overline="Галерея" title="Примеры работ" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {s.gallery.map((g, i) => (
                <Reveal key={g.src} delay={(i % 3) * 0.07}>
                  <figure className="img-zoom card-hover overflow-hidden rounded-3xl border border-line bg-card">
                    <img src={g.src} alt={g.cap} loading="lazy" className="h-64 w-full object-cover" />
                    {g.cap && <figcaption className="px-5 py-4 text-sm text-mut">{g.cap}</figcaption>}
                  </figure>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      {s.faq && (
        <section className="mx-auto max-w-4xl px-5 py-20">
          <SectionHead overline="FAQ" title="Частые вопросы" />
          <Reveal>
            <Accordion items={s.faq} />
          </Reveal>
        </section>
      )}

      {s.cta && (
        <section className="mx-auto max-w-7xl px-5 pb-6">
          <Reveal>
            <div className="flex flex-col items-start justify-between gap-8 rounded-3xl border border-line bg-card p-8 md:flex-row md:items-center md:p-12">
              <div>
                <h2 className="display-h text-2xl font-bold md:text-3xl">{s.cta.title}</h2>
                {s.cta.text && <p className="mt-3 max-w-2xl text-mut">{s.cta.text}</p>}
                <div className="mt-5 flex flex-wrap gap-5 text-sm">
                  <a href={PHONE_HREF} className="font-bold text-accent">{PHONE}</a>
                  <a href={TG} target="_blank" rel="noreferrer" className="font-bold text-accent">Telegram</a>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Btn onClick={() => openLead(s.title)}>Оставить заявку</Btn>
                <Btn to="/kontakty" variant="ghost">Контакты</Btn>
              </div>
            </div>
          </Reveal>
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
