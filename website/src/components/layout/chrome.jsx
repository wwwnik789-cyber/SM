import { useEffect, useState } from "react";
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useScroll, useSpring } from "motion/react";
import { useUI } from "../../lib/store";
import { ArrowUpRight, Check, Close } from "../ui/Icons";

/** Полоса прогресса скролла (тренд: kinetic scroll feedback) */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 28, mass: 0.4 });
  return <motion.div style={{ scaleX }} className="fixed inset-x-0 top-0 z-[75] h-[3px] origin-left bg-accent" />;
}

/** Мягкое свечение, следующее за курсором (только desktop, уважает reduced-motion) */
export function CursorGlow() {
  const reduce = useReducedMotion();
  const [fine, setFine] = useState(false);
  const x = useMotionValue(-400);
  const y = useMotionValue(-400);
  const sx = useSpring(x, { stiffness: 60, damping: 18 });
  const sy = useSpring(y, { stiffness: 60, damping: 18 });

  useEffect(() => {
    setFine(window.matchMedia("(pointer: fine)").matches);
    const on = (e) => {
      x.set(e.clientX);
      y.set(e.clientY);
    };
    window.addEventListener("pointermove", on, { passive: true });
    return () => window.removeEventListener("pointermove", on);
  }, [x, y]);

  if (reduce || !fine) return null;
  return (
    <motion.div
      aria-hidden="true"
      style={{ left: sx, top: sy }}
      className="pointer-events-none fixed z-0 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-[0.16] blur-3xl"
    >
      <div className="h-full w-full rounded-full bg-[radial-gradient(circle_at_center,var(--sm-accent),transparent_65%)]" />
    </motion.div>
  );
}

export function Toast() {
  const { toast } = useUI();
  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.97 }}
          className="glass fixed bottom-6 left-1/2 z-[90] flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-line px-5 py-4 text-sm font-semibold shadow-2xl"
        >
          <span className="rounded-full bg-acid p-1 text-black"><Check size={13} /></span>
          {toast}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function CookieBanner() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("sm-cookie-ok")) setShow(true);
  }, []);
  if (!show) return null;
  return (
    <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="fixed bottom-5 right-5 z-[80] max-w-sm rounded-2xl border border-line bg-card p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-mut">Мы используем файлы cookie, чтобы обеспечить наилучшую работу сайта.</p>
        <button onClick={() => setShow(false)} aria-label="Закрыть" className="text-mut hover:text-ink"><Close size={16} /></button>
      </div>
      <button
        onClick={() => {
          localStorage.setItem("sm-cookie-ok", "1");
          setShow(false);
        }}
        className="mt-4 rounded-xl bg-accent px-5 py-2.5 font-display text-xs uppercase tracking-widest text-white"
      >
        Хорошо
      </button>
    </motion.div>
  );
}

export function BackToTop() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const on = () => setShow(window.scrollY > 900);
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <AnimatePresence>
      {show && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          aria-label="Наверх"
          className="fixed bottom-6 left-6 z-[80] rounded-2xl border border-line bg-card p-3.5 text-accent shadow-xl transition-colors hover:border-accent"
        >
          <ArrowUpRight size={18} />
        </motion.button>
      )}
    </AnimatePresence>
  );
}

/** Короткий прелоадер с логотипом при первом заходе в сессию */
export function Preloader() {
  const [show, setShow] = useState(() => !sessionStorage.getItem("sm-visited"));
  useEffect(() => {
    if (!show) return;
    sessionStorage.setItem("sm-visited", "1");
    const t = setTimeout(() => setShow(false), 1400);
    return () => clearTimeout(t);
  }, [show]);
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          exit={{ opacity: 0, scale: 1.06 }}
          transition={{ duration: 0.5, ease: [0.6, 0, 0.2, 1] }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-bg"
        >
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-display text-4xl font-black tracking-tight"
          >
            SM<span className="text-accent">•</span>PRODUCTION
          </motion.div>
          <div className="h-[2px] w-40 overflow-hidden rounded bg-line">
            <motion.div initial={{ x: "-100%" }} animate={{ x: "100%" }} transition={{ duration: 1.1, ease: "easeInOut" }} className="h-full w-1/2 bg-accent" />
          </div>
          <p className="font-display text-[10px] uppercase tracking-[0.4em] text-mut">event · brand · decor</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
