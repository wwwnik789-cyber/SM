import { useMemo, useState } from "react";
import { letters, reviewCategories, reviews } from "../data/reviews";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Chip } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Star } from "../components/ui/Icons";

export default function Reviews() {
  usePageMeta("Отзывы клиентов о SM Production", "Отзывы и благодарственные письма клиентов: фотозоны, баннеры, стенды, оформление сцен и застройка мероприятий.");
  const [cat, setCat] = useState("Все");
  const list = useMemo(() => (cat === "Все" ? reviews : reviews.filter((r) => r.cat === cat)), [cat]);

  return (
    <>
      <PageHero overline="Отзывы" title={<>Что говорят <span className="text-accent">наши клиенты</span></>} text="Посмотрите отзывы, которые пишут клиенты о нашей работе — от фотозон до комплексной застройки мероприятий.">
        <div className="mt-8 flex flex-wrap gap-2">
          {reviewCategories.map((c) => (
            <Chip key={c} active={cat === c} onClick={() => setCat(c)}>{c}</Chip>
          ))}
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="columns-1 gap-5 md:columns-2 lg:columns-3 [&>*]:mb-5">
          {list.map((r, i) => (
            <Reveal key={r.name + r.cat} delay={(i % 3) * 0.05}>
              <div className="card-hover break-inside-avoid rounded-3xl border border-line bg-card p-7">
                <div className="flex items-center justify-between">
                  <span className="display-h flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-lg font-black text-white">{r.name[0]}</span>
                  <span className="flex gap-0.5 text-acid">{[...Array(5)].map((_, s) => <Star key={s} size={13} />)}</span>
                </div>
                <p className="mt-5 text-sm leading-relaxed text-ink/85">«{r.text}»</p>
                <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
                  <p className="font-display text-sm font-bold">{r.name}</p>
                  <span className="rounded-full border border-line px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-mut">{r.cat}</span>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-24">
        <h2 className="display-h mb-10 text-2xl font-bold md:text-3xl">Благодарственные письма</h2>
        <div className="grid gap-5 md:grid-cols-2">
          {letters.map((l, i) => (
            <Reveal key={l.from} delay={i * 0.08}>
              <figure className="relative h-full rounded-3xl border border-line bg-bg2 p-8">
                <span className="display-h absolute -top-5 left-7 font-display text-7xl font-black text-accent">“</span>
                <blockquote className="pt-4 text-base leading-relaxed text-ink/85">{l.text}</blockquote>
                <figcaption className="mt-6 border-t border-line pt-4 text-sm">
                  <p className="font-display font-bold">{l.from}</p>
                  <p className="text-mut">{l.sign}</p>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
