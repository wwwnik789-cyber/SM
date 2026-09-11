import { Link, useParams } from "react-router-dom";
import { getService, services } from "../data/services";
import { usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Btn, ArrowLink } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Check, Clock, MapPin } from "../components/ui/Icons";
import { fmtMoney } from "../lib/format";
import { useUI } from "../lib/store";

export default function ServiceDetail() {
  const { slug } = useParams();
  const s = getService(slug);
  usePageMeta(s ? `${s.title} — SM-Production` : "Услуга не найдена", s?.short);
  const { openLead } = useUI();
  if (!s) return <NotFound />;

  const related = services.filter((x) => x.slug !== s.slug && x.category === s.category).slice(0, 3);

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
              <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">{s.category}</p>
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
