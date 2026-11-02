import { Link, useParams } from "react-router-dom";
import { getCase, portfolio } from "../data/portfolio";
import { usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Reveal } from "../components/ui/motion";
import { Btn, ArrowLink } from "../components/ui/bits";
import { Check, MapPin } from "../components/ui/Icons";
import { useUI } from "../lib/store";

export default function PortfolioDetail() {
  const { slug } = useParams();
  const p = getCase(slug);
  usePageMeta(p ? `${p.title} — кейс SM-Production` : "Кейс не найден", p?.task);
  const { openLead } = useUI();
  if (!p) return <NotFound />;

  const idx = portfolio.findIndex((x) => x.slug === slug);
  const next = portfolio[(idx + 1) % portfolio.length];

  return (
    <>
      <section className="relative overflow-hidden pt-36 md:pt-44">
        <div className="relative mx-auto max-w-7xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/portfolio" className="hover:text-ink">Портфолио</Link> / <span className="text-ink">{p.title}</span>
          </nav>
          <Reveal>
            <div className="flex flex-wrap items-center gap-2">
              {p.tags.map((t) => <span key={t} className="rounded-full border border-line px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-mut">{t}</span>)}
              <span className="rounded-full bg-accent px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white">{p.year}</span>
            </div>
            <h1 className="display-h mt-5 max-w-4xl text-4xl font-black md:text-6xl">{p.title}</h1>
            <p className="mt-4 flex items-center gap-2 text-mut"><MapPin size={15} /> {p.place} · клиент: {p.client}</p>
          </Reveal>
          <Reveal delay={0.15}>
            <div className="img-zoom mt-10 overflow-hidden rounded-3xl border border-line">
              <img src={p.image} alt={p.title} className="max-h-[560px] w-full object-cover" />
            </div>
          </Reveal>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <Reveal><div className="rounded-3xl border border-line bg-card p-7"><h2 className="font-display text-xs uppercase tracking-[0.24em] text-accent">Задача</h2><p className="mt-4 leading-relaxed text-ink/85">{p.task}</p></div></Reveal>
          <Reveal delay={0.08}><div className="rounded-3xl border border-line bg-card p-7"><h2 className="font-display text-xs uppercase tracking-[0.24em] text-acid">Решение</h2><p className="mt-4 leading-relaxed text-ink/85">{p.solution}</p></div></Reveal>
          <Reveal delay={0.16}>
            <div className="rounded-3xl border border-line bg-card p-7">
              <h2 className="font-display text-xs uppercase tracking-[0.24em] text-mut">Инструменты</h2>
              <ul className="mt-4 space-y-2.5">
                {p.tools.map((t) => <li key={t} className="flex items-start gap-2.5 text-sm"><span className="mt-0.5 text-accent"><Check size={13} /></span>{t}</li>)}
              </ul>
            </div>
          </Reveal>
        </div>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          {p.metrics.map(([v, l]) => (
            <div key={l} className="rounded-3xl border border-line bg-bg2 p-7 text-center">
              <p className="display-h text-4xl font-black text-accent">{v}</p>
              <p className="mt-2 text-sm text-mut">{l}</p>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-wrap items-center justify-between gap-6 border-t border-line pt-10">
          <div>
            <p className="text-sm text-mut">Следующий кейс</p>
            <Link to={`/portfolio/${next.slug}`} className="display-h mt-1 inline-block text-2xl font-bold hover:text-accent">{next.title} →</Link>
          </div>
          <div className="flex gap-4">
            <ArrowLink to="/portfolio">Все кейсы</ArrowLink>
            <Btn onClick={() => openLead("Хочу похожий проект")}>Хочу похожий проект</Btn>
          </div>
        </div>
      </section>
    </>
  );
}
