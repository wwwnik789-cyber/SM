import { Link, useParams } from "react-router-dom";
import { getPost, posts } from "../data/blog";
import { usePageMeta } from "../hooks/usePageMeta";
import NotFound from "./NotFound";
import { Reveal } from "../components/ui/motion";
import { ArrowLink } from "../components/ui/bits";
import { fmtDate } from "../lib/format";

export default function BlogPost() {
  const { slug } = useParams();
  const p = getPost(slug);
  usePageMeta(p ? `${p.title} — блог SM-Production` : "Статья не найдена", p?.excerpt);
  if (!p) return <NotFound />;

  const related = posts.filter((x) => x.slug !== slug && x.tag === p.tag).slice(0, 2);

  return (
    <>
      <article className="relative pt-36 md:pt-44">
        <div className="grid-bg mask-fade-b absolute inset-x-0 top-0 h-[520px] opacity-50" />
        <div className="relative mx-auto max-w-3xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/blog" className="hover:text-ink">Блог</Link> / <span className="text-ink">{p.tag}</span>
          </nav>
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">{p.tag} · {fmtDate(p.date)} · {p.read} мин чтения</p>
            <h1 className="display-h mt-5 text-3xl font-black md:text-5xl">{p.title}</h1>
          </Reveal>
          <Reveal delay={0.12}>
            <img src={p.cover} alt="" className="mt-10 max-h-[460px] w-full rounded-3xl border border-line object-cover" />
          </Reveal>

          <div className="mt-12 space-y-7">
            {p.content.map((b, i) => (
              <Reveal key={i}>
                {b.h && <h2 className="display-h mb-3 text-2xl font-bold">{b.h}</h2>}
                {b.p && <p className="text-lg leading-relaxed text-ink/85">{b.p}</p>}
                {b.list && (
                  <ul className="space-y-3">
                    {b.list.map((li) => (
                      <li key={li} className="flex items-start gap-3 text-lg leading-relaxed text-ink/85">
                        <span className="mt-2.5 h-2 w-2 shrink-0 rotate-45 bg-accent" />{li}
                      </li>
                    ))}
                  </ul>
                )}
              </Reveal>
            ))}
          </div>

          <div className="mt-14 rounded-3xl border border-line bg-card p-7">
            <p className="font-display text-sm font-bold">Поделиться мнением или задать вопрос</p>
            <p className="mt-2 text-sm text-mut">Позвоните <a className="text-accent" href="tel:+74957990019">+7 495 799-00-19</a> — личный руководитель проектов на связи 24/7.</p>
          </div>
        </div>
      </article>

      {related.length > 0 && (
        <section className="mx-auto max-w-3xl px-5 py-16">
          <h2 className="display-h mb-6 text-2xl font-bold">Читать ещё</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {related.map((r) => (
              <Link key={r.slug} to={`/blog/${r.slug}`} className="card-hover group rounded-2xl border border-line bg-card p-5">
                <p className="font-display text-[10px] uppercase tracking-[0.24em] text-accent">{r.tag}</p>
                <p className="mt-2 font-bold leading-snug group-hover:text-accent">{r.title}</p>
              </Link>
            ))}
          </div>
          <div className="mt-8"><ArrowLink to="/blog">Все статьи</ArrowLink></div>
        </section>
      )}
    </>
  );
}
