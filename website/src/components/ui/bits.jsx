import { AnimatePresence, motion } from "motion/react";
import { Link } from "react-router-dom";
import { useState } from "react";
import { ArrowRight, Plus } from "./Icons";

export function Btn({ to, onClick, children, variant = "primary", className = "", type }) {
  const base =
    "btn-sheen inline-flex items-center justify-center gap-2.5 font-display text-[13px] uppercase tracking-[0.14em] transition-all duration-300 px-7 py-4 rounded-xl select-none";
  const styles = {
    primary: "bg-accent text-white hover:brightness-110 active:scale-[0.98] shadow-[0_10px_38px_-10px_var(--sm-accent)]",
    ghost: "border border-line text-ink hover:border-accent hover:text-accent",
    acid: "bg-acid text-black hover:brightness-105 active:scale-[0.98]",
  };
  const cls = `${base} ${styles[variant]} ${className}`;
  if (to)
    return (
      <Link to={to} className={cls} onClick={onClick}>
        {children}
      </Link>
    );
  return (
    <button type={type || "button"} className={cls} onClick={onClick}>
      {children}
    </button>
  );
}

export function SectionHead({ overline, title, text, className = "" }) {
  return (
    <div className={`mb-12 md:mb-16 ${className}`}>
      {overline && (
        <div className="mb-4 flex items-center gap-3">
          <span className="h-2 w-2 rotate-45 bg-accent" />
          <span className="font-display text-xs uppercase tracking-[0.28em] text-mut">{overline}</span>
        </div>
      )}
      <h2 className="display-h text-3xl font-bold md:text-5xl">{title}</h2>
      {text && <p className="mt-5 max-w-2xl text-base leading-relaxed text-mut md:text-lg">{text}</p>}
    </div>
  );
}

export function Chip({ active, children, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm font-semibold transition-all duration-300 ${
        active ? "border-accent bg-accent text-white" : "border-line text-mut hover:border-ink hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

export function Accordion({ items, single = true }) {
  const [open, setOpen] = useState(single ? null : []);
  const isOpen = (i) => (single ? open === i : open.includes(i));
  const toggle = (i) => {
    if (single) setOpen(open === i ? null : i);
    else setOpen((o) => (o.includes(i) ? o.filter((x) => x !== i) : [...o, i]));
  };

  return (
    <div className="divide-y divide-line border-y border-line">
      {items.map((it, i) => (
        <div key={i}>
          <button
            className="group flex w-full items-center justify-between gap-6 py-6 text-left"
            onClick={() => toggle(i)}
            aria-expanded={isOpen(i)}
          >
            <span className="font-display text-base font-semibold md:text-lg group-hover:text-accent transition-colors">
              {it.q}
            </span>
            <span
              className={`shrink-0 rounded-full border border-line p-2 transition-transform duration-300 ${isOpen(i) ? "rotate-45 border-accent text-accent" : ""}`}
            >
              <Plus size={16} />
            </span>
          </button>
          <AnimatePresence initial={false}>
            {isOpen(i) && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.35, ease: [0.2, 0.65, 0.25, 1] }}
                className="overflow-hidden"
              >
                <div className="max-w-3xl pb-7 leading-relaxed text-mut">{it.a}</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}

export function ArrowLink({ to, children, className = "" }) {
  return (
    <Link to={to} className={`group inline-flex items-center gap-2 font-display text-sm uppercase tracking-[0.14em] text-accent ${className}`}>
      <span className="link-underline">{children}</span>
      <ArrowRight size={16} className="transition-transform duration-300 group-hover:translate-x-1.5" />
    </Link>
  );
}
