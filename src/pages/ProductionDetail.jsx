import { Link, useParams } from "react-router-dom";
import { getProduction, production } from "../data/production";
import { usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Reveal } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { Check } from "../components/ui/Icons";
import { useUI } from "../lib/store";

export default function ProductionDetail() {
  const { slug } = useParams();
  const p = getProduction(slug);
  usePageMeta(p ? `${p.title} — производство на заказ | SM-Production` : "Не найдено", p?.short);
  const { openLead } = useUI();
  if (!p) return <NotFound />;

  return (
    <>
      <section className="relative overflow-hidden pt-36 md:pt-44">
        <div className="grid-bg mask-fade-b absolute inset-0 opacity-50" />
        <div className="relative mx-auto max-w-7xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/proizvodstvo" className="hover:text-ink">Производство</Link> / <span className="text-ink">{p.title}</span>
          </nav>
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <Reveal>
              <p className="text-outline display-h text-7xl font-black">{p.num}</p>
              <h1 className="display-h mt-2 text-4xl font-black md:text-5xl">{p.title}</h1>
              <p className="mt-6 max-w-xl text-lg text-mut">{p.short}</p>
              <Btn onClick={() => openLead(p.title)} className="mt-8">Заказать {p.title.toLowerCase()}</Btn>
            </Reveal>
            <Reveal delay={0.12}>
              <img src={p.image} alt={p.title} className="rounded-3xl border border-line object-cover max-h-[420px] w-full" />
            </Reveal>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {p.sections.map((sec, i) => (
            <Reveal key={sec.h} delay={i * 0.07}>
              <div className="h-full rounded-3xl border border-line bg-card p-7">
                <h2 className="font-display text-lg font-bold">{sec.h}</h2>
                <ul className="mt-5 space-y-3">
                  {sec.list.map((li) => (
                    <li key={li} className="flex items-start gap-3 text-sm leading-relaxed text-mut">
                      <span className="mt-0.5 shrink-0 text-acid"><Check size={14} /></span>{li}
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-14 flex flex-wrap items-center justify-between gap-6 rounded-3xl border border-line bg-bg2 p-8">
          <h2 className="display-h text-2xl font-bold">Другие направления производства</h2>
          <div className="flex flex-wrap gap-2">
            {production.filter((x) => x.slug !== slug).map((x) => (
              <Link key={x.slug} to={`/proizvodstvo/${x.slug}`} className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-mut transition-colors hover:border-accent hover:text-accent">
                {x.title}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
