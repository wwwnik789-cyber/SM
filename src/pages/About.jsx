import { companyHistory, companyStats, values } from "../data/team";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Counter, Reveal } from "../components/ui/motion";
import { SectionHead, Btn } from "../components/ui/bits";
import { useUI } from "../lib/store";

export default function About() {
  usePageMeta("О компании SM-Production — производство полного цикла", "SM Production — производство полного цикла: комплексный спектр услуг в сфере оформления и брендирования мероприятий любого уровня.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="О компании" title={<>Производство полного цикла <span className="text-accent">для ваших событий</span></>} text="SM Production предоставляет комплексный спектр услуг в сфере оформления и брендирования мероприятий любого уровня — от концепции до реализации и сопровождения." />

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-10 lg:grid-cols-2">
          <Reveal>
            <div className="space-y-5 text-lg leading-relaxed text-ink/85">
              <p>Мы помогаем клиентам создавать эффектные и запоминающиеся мероприятия: берём на себя декорирование, брендирование, производство конструкций и медиаподдержку.</p>
              <p>Собственные производственные мощности — более 750 м² в Москве и Санкт-Петербурге. Работаем круглосуточно, печатаем баннер за 3 часа и монтируем конструкции 24/7.</p>
              <p>Наша команда находится в постоянном поиске новых идей и нестандартных решений, отслеживая тренды и тенденции в дизайне, чтобы предлагать вам оригинальные и креативные концепции.</p>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="img-zoom overflow-hidden rounded-3xl border border-line">
              <img src="/media/workshop.jpg" alt="Производство SM-Production" className="h-full w-full object-cover" />
            </div>
          </Reveal>
        </div>

        <div className="mt-20 grid gap-6 md:grid-cols-4">
          {companyStats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.07}>
              <div className="rounded-3xl border border-line bg-card p-7 text-center">
                <p className="display-h text-4xl font-black text-accent"><Counter value={s.value} suffix={s.suffix} /></p>
                <p className="mt-2 text-sm text-mut">{s.label}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-5 py-24">
        <SectionHead overline="История" title="Таймлайн компании" />
        <div className="space-y-0">
          {companyHistory.map((h, i) => (
            <Reveal key={h.year} delay={i * 0.05}>
              <div className="group grid gap-4 border-t border-line py-7 md:grid-cols-[140px_1fr] md:gap-10">
                <p className="display-h text-3xl font-black text-accent">{h.year}</p>
                <p className="text-base leading-relaxed text-ink/85 transition-transform duration-300 group-hover:translate-x-2">{h.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-bg2 py-20">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Ценности" title="Почему выбирают нас" />
          <div className="grid gap-4 md:grid-cols-4">
            {values.map((v, i) => (
              <Reveal key={v.title} delay={i * 0.06}>
                <div className="card-hover h-full rounded-3xl border border-line bg-card p-7 text-center">
                  <p className="display-h text-2xl font-black text-acid">0{i + 1}</p>
                  <h3 className="mt-3 font-display text-lg font-bold">{v.title}</h3>
                  <p className="mt-3 text-sm text-mut">{v.text}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Btn onClick={() => openLead()}>Получить консультацию</Btn>
          </div>
        </div>
      </section>
    </>
  );
}
