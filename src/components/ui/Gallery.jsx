import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Close } from "./Icons";
import { Reveal } from "./motion";
import { useLockBody } from "../../hooks/usePageMeta";

/** Сетка работ с полноэкранным просмотром и перелистыванием стрелками / клавиатурой */
export default function Gallery({ items, className = "" }) {
  const [index, setIndex] = useState(null);
  const open = index !== null;
  useLockBody(open);

  const step = useCallback(
    (d) => setIndex((i) => (i === null ? i : (i + d + items.length) % items.length)),
    [items.length]
  );

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") setIndex(null);
      if (e.key === "ArrowRight") step(1);
      if (e.key === "ArrowLeft") step(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, step]);

  const current = open ? items[index] : null;

  return (
    <>
      <div className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-3 ${className}`}>
        {items.map((it, i) => (
          <Reveal key={it.src + i} delay={(i % 3) * 0.06}>
            <button
              type="button"
              onClick={() => setIndex(i)}
              className="card-hover img-zoom group block h-full w-full overflow-hidden rounded-3xl border border-line bg-card text-left"
              aria-label={`Открыть работу: ${it.title}`}
            >
              <div className="relative overflow-hidden">
                <img src={it.src} alt={it.title} loading="lazy" className="h-60 w-full object-cover" />
                {it.tag && (
                  <span className="absolute left-4 top-4 rounded-full bg-black/55 px-3 py-1.5 font-display text-[10px] uppercase tracking-widest text-white backdrop-blur">
                    {it.tag}
                  </span>
                )}
                <span className="absolute right-4 top-4 rounded-full border border-white/30 p-2 text-white opacity-0 backdrop-blur transition-opacity group-hover:opacity-100">
                  <ArrowRight size={14} className="-rotate-45" />
                </span>
              </div>
              <div className="p-5">
                <p className="font-display text-sm font-bold group-hover:text-accent">{it.title}</p>
                {it.meta && <p className="mt-1.5 text-xs leading-relaxed text-mut">{it.meta}</p>}
              </div>
            </button>
          </Reveal>
        ))}
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-[95] flex items-center justify-center bg-black/85 p-4 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIndex(null)}
            role="dialog"
            aria-modal="true"
            aria-label={current.title}
          >
            <button
              type="button"
              onClick={() => setIndex(null)}
              className="absolute right-5 top-5 rounded-full border border-white/25 p-3 text-white transition-colors hover:border-accent hover:text-accent"
              aria-label="Закрыть просмотр"
            >
              <Close size={18} />
            </button>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); step(-1); }}
              className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full border border-white/25 p-3 text-white transition-colors hover:border-accent hover:text-accent md:left-8"
              aria-label="Предыдущая работа"
            >
              <ArrowRight size={18} className="rotate-180" />
            </button>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); step(1); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full border border-white/25 p-3 text-white transition-colors hover:border-accent hover:text-accent md:right-8"
              aria-label="Следующая работа"
            >
              <ArrowRight size={18} />
            </button>
            <motion.figure
              key={current.src}
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.28 }}
              className="max-h-full w-full max-w-5xl"
              onClick={(e) => e.stopPropagation()}
            >
              <img src={current.src} alt={current.title} className="max-h-[76vh] w-full rounded-2xl object-contain" />
              <figcaption className="mt-4 text-center">
                <p className="font-display text-sm font-bold text-white">{current.title}</p>
                {current.meta && <p className="mt-1 text-xs text-white/60">{current.meta}</p>}
                <p className="mt-2 text-[11px] uppercase tracking-[0.2em] text-white/40">{index + 1} / {items.length}</p>
              </figcaption>
            </motion.figure>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
