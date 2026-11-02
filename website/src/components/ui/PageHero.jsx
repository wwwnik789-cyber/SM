import { motion } from "motion/react";
import { Reveal } from "./motion";

export default function PageHero({ overline, title, text, children }) {
  return (
    <section className="relative overflow-hidden pb-14 pt-36 md:pb-20 md:pt-44">
      <div className="grid-bg mask-fade-b absolute inset-0 opacity-60" aria-hidden="true" />
      <div className="pointer-events-none absolute -top-40 right-[-10%] h-[480px] w-[480px] rounded-full bg-accent/15 blur-[130px]" aria-hidden="true" />
      <div className="relative mx-auto max-w-7xl px-5">
        <Reveal>
          <div className="mb-5 flex items-center gap-3">
            <span className="h-2 w-2 rotate-45 bg-accent" />
            <span className="font-display text-xs uppercase tracking-[0.3em] text-mut">{overline}</span>
          </div>
        </Reveal>
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.2, 0.65, 0.25, 1] }}
          className="display-h max-w-4xl text-4xl font-black md:text-6xl"
        >
          {title}
        </motion.h1>
        {text && (
          <Reveal delay={0.15}>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-mut">{text}</p>
          </Reveal>
        )}
        {children && <Reveal delay={0.2}>{children}</Reveal>}
      </div>
    </section>
  );
}
