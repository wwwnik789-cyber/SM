import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { portfolio, portfolioTags } from "../data/portfolio";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Chip } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { ArrowUpRight, MapPin } from "../components/ui/Icons";

export default function Portfolio() {
  usePageMeta("Портфолио — фотозоны, стенды и декорации для мероприятий | SM-Production", "Выполненные работы SM-Production: застройка фестивалей, конференции, световые конструкции и имиджевые фотозоны.");
  const [tag, setTag] = useState("Все");
  const list = useMemo(() => (tag === "Все" ? portfolio : portfolio.filter((p) => p.tags.includes(tag))), [tag]);

  return (
    <>
      <PageHero overline="Выполненные работы" title={<>Проекты, которыми <span className="text-accent">мы гордимся</span></>} text="Команда SM — ваш надёжный партнёр в мире оформления и брендирования мероприятий любого уровня.">
        <div className="mt-8 flex flex-wrap gap-2">
          {portfolioTags.map((t) => (
            <Chip key={t} active={tag === t} onClick={() => setTag(t)}>{t}</Chip>
          ))}
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-5 md:grid-cols-2">
          {list.map((p, i) => (
            <Reveal key={p.slug} delay={(i % 2) * 0.08}>
              <Link to={`/portfolio/${p.slug}`} className="card-hover img-zoom group relative block overflow-hidden rounded-3xl border border-line">
                <img src={p.image} alt={p.title} loading="lazy" className="h-[380px] w-full object-cover md:h-[440px]" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/25 to-transparent" />
                <div className="absolute left-5 top-5 flex flex-wrap gap-2">
                  {p.tags.map((t) => (
                    <span key={t} className="rounded-full bg-black/50 px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white backdrop-blur">{t}</span>
                  ))}
                </div>
                <div className="absolute inset-x-0 bottom-0 p-7">
                  <p className="font-display text-[11px] uppercase tracking-[0.24em] text-acid">{p.year} · {p.client}</p>
                  <h2 className="display-h mt-2 text-2xl font-bold text-white">{p.title}</h2>
                  <p className="mt-2 flex items-center gap-2 text-xs text-white/65"><MapPin size={13} /> {p.place}</p>
                </div>
                <span className="absolute right-6 top-6 rounded-full border border-white/30 p-3 text-white opacity-0 transition-all duration-300 group-hover:opacity-100"><ArrowUpRight size={16} /></span>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
