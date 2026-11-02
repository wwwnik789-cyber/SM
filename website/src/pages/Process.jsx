import { useRef } from "react";
import { motion, useScroll, useSpring } from "motion/react";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { useUI } from "../lib/store";

const steps = [
  { n: "01", t: "Обсуждаем задачу и готовим решение", items: ["Вы оставляете заявку — мы оперативно связываемся для глубокой консультации.", "Анализируем цели, бюджет и особенности, предлагая эффективные и экономичные варианты.", "Результат — прозрачное коммерческое предложение и ТЗ, согласованные до мелочей."] },
  { n: "02", t: "Создаём концепцию и изготавливаем", items: ["Дизайнеры разрабатывают креативные и уникальные концепции.", "Предоставляем 3D-визуализации для наглядности.", "Собственное производство изготавливает конструкции из качественных материалов, контролируя сроки."] },
  { n: "03", t: "Организуем монтаж и обеспечиваем работу", items: ["Берём на себя логистику: доставляем со склада и профессионально монтируем на площадке.", "На протяжении события команда обеспечивает техподдержку и оперативно решает вопросы."] },
  { n: "04", t: "Производим демонтаж и собираем отзывы", items: ["После мероприятия аккуратно демонтируем и вывозим конструкции.", "Собираем впечатления и пожелания, чтобы непрерывно улучшать сервис."] },
];

export default function Process() {
  usePageMeta("Процессы работы — этапы организации мероприятий | SM-Production", "Как мы превращаем ваши идеи в эффектные решения: четыре этапа от заявки до демонтажа.");
  const { openLead } = useUI();
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 0.7", "end 0.5"] });
  const height = useSpring(scrollYProgress, { stiffness: 90, damping: 24 });

  return (
    <>
      <PageHero overline="Процессы" title={<>Как ваши идеи воплощаются <span className="text-accent">в реальность</span></>} text="Отлаженная схема работы: прозрачные этапы, фиксированные сроки и постоянный контакт с личным менеджером." />

      <section ref={ref} className="mx-auto max-w-5xl px-5 pb-24">
        <div className="relative">
          {/* progress line */}
          <div className="absolute left-5 top-0 h-full w-px bg-line md:left-1/2" aria-hidden="true" />
          <motion.div style={{ scaleY: height }} className="absolute left-5 top-0 h-full w-[3px] origin-top bg-accent md:left-1/2" aria-hidden="true" />

          {steps.map((s, i) => (
            <div key={s.n} className={`relative mb-16 pl-16 md:w-1/2 md:pl-0 ${i % 2 === 0 ? "md:pr-16 md:text-right" : "md:ml-auto md:pl-16"}`}>
              {/* node */}
              <span className={`absolute top-2 left-5 -translate-x-1/2 md:left-auto ${i % 2 === 0 ? "md:right-0 md:translate-x-1/2" : "md:left-0 md:-translate-x-1/2"}`}>
                <span className="block h-4 w-4 rotate-45 border-2 border-accent bg-bg" />
              </span>
              <Reveal>
                <p className="text-outline display-h text-6xl font-black">{s.n}</p>
                <h2 className="display-h mt-3 text-2xl font-bold">{s.t}</h2>
                <ul className={`mt-5 space-y-3 text-sm leading-relaxed text-mut ${i % 2 === 0 ? "md:ml-auto" : ""} max-w-md`}>
                  {s.items.map((it) => <li key={it}>{it}</li>)}
                </ul>
              </Reveal>
            </div>
          ))}
        </div>

        <Reveal>
          <div className="mt-8 rounded-3xl border border-line bg-card p-8 text-center md:p-12">
            <h2 className="display-h text-2xl font-bold md:text-3xl">Готовы пройти этот путь вместе?</h2>
            <p className="mx-auto mt-3 max-w-xl text-mut">Оставьте заявку — и мы начнём с первого этапа уже сегодня.</p>
            <div className="mt-7"><Btn onClick={() => openLead()}>Получить консультацию</Btn></div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
