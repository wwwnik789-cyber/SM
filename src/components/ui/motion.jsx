import { motion, useInView, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";

/** Плавное появление блока при скролле */
export function Reveal({ children, delay = 0, y = 26, className }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: reduce ? 0 : y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.7, delay, ease: [0.2, 0.65, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

/** Анимированный счётчик цифр */
export function Counter({ value, suffix = "", duration = 1.4, className }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [n, setN] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let raf;
    const t0 = performance.now();
    const tick = (t) => {
      const p = Math.min(1, (t - t0) / (duration * 1000));
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.round(value * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);

  return (
    <span ref={ref} className={className}>
      {n}
      {suffix}
    </span>
  );
}

/** Бегущая строка */
export function Marquee({ items, className = "", speed = 32 }) {
  const row = (
    <div className="flex shrink-0 items-center gap-10 pr-10" aria-hidden="true">
      {items.map((t, i) => (
        <span key={i} className="flex items-center gap-10 whitespace-nowrap">
          <span className="font-display text-sm uppercase tracking-[0.2em] text-mut">{t}</span>
          <span className="h-1.5 w-1.5 rotate-45 bg-accent" />
        </span>
      ))}
    </div>
  );
  return (
    <div className={`mask-fade-x overflow-hidden ${className}`}>
      <div className="flex w-max" style={{ animation: `marquee ${speed}s linear infinite` }}>
        {row}
        {row}
      </div>
    </div>
  );
}
