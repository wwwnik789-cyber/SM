import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { blogTags, posts } from "../data/blog";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Chip } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Search } from "../components/ui/Icons";
import { fmtDate } from "../lib/format";

export default function Blog() {
  usePageMeta("Блог об оформлении мероприятий: кейсы и советы | SM-Production", "Новости об оформлении мероприятий, производственных процессах и интересных проектах SM-Production.");
  const [tag, setTag] = useState("Все");
  const [q, setQ] = useState("");
  const list = useMemo(() => {
    let l = tag === "Все" ? posts : posts.filter((p) => p.tag === tag);
    if (q.trim()) l = l.filter((p) => (p.title + p.excerpt).toLowerCase().includes(q.toLowerCase()));
    return [...l].sort((a, b) => b.date.localeCompare(a.date));
  }, [tag, q]);

  return (
    <>
      <PageHero overline="Новости SM-Production" title={<>Блог: кейсы, советы <span className="text-accent">и тренды</span></>} text="Публикуем новости об оформлении мероприятий, производственных процессах и интересных проектах нашей компании.">
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 rounded-xl border border-line bg-card px-4 py-2.5">
            <Search size={15} className="text-mut" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Поиск по статьям…" className="w-48 bg-transparent text-sm outline-none" />
          </label>
          {blogTags.map((t) => (
            <Chip key={t} active={tag === t} onClick={() => setTag(t)}>{t}</Chip>
          ))}
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        {list.length === 0 && <p className="py-20 text-center text-mut">По запросу ничего не нашлось. Попробуйте «фотозона».</p>}
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {list.map((p, i) => (
            <Reveal key={p.slug} delay={(i % 3) * 0.06}>
              <Link to={`/blog/${p.slug}`} className="card-hover img-zoom group flex h-full flex-col overflow-hidden rounded-3xl border border-line bg-card">
                <div className="overflow-hidden"><img src={p.cover} alt="" loading="lazy" className="h-52 w-full object-cover" /></div>
                <div className="flex flex-1 flex-col p-6">
                  <p className="font-display text-[10px] uppercase tracking-[0.24em] text-accent">{p.tag} · {fmtDate(p.date)}</p>
                  <h2 className="display-h mt-3 flex-1 text-lg font-bold leading-snug group-hover:text-accent">{p.title}</h2>
                  <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-mut">{p.excerpt}</p>
                  <p className="mt-4 border-t border-line pt-3 text-xs text-mut">Читать · {p.read} мин</p>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
