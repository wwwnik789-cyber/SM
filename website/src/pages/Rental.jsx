import { rental, rentalSteps } from "../data/rental";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn, SectionHead } from "../components/ui/bits";
import { useUI } from "../lib/store";
import { faq } from "../data/faq";
import { Accordion } from "../components/ui/bits";

export default function Rental() {
  usePageMeta("Аренда оборудования для мероприятий — свет, звук, мебель | SM-Production", "Аренда светового и звукового оборудования, мебели и конструкций для мероприятий. Доставка, монтаж и демонтаж под ключ.");
  const { openLead } = useUI();
  const rentalFaq = faq.filter((f) => f.q.includes("аренд") || f.q.includes("бронир") || f.q.includes("доставка"));

  return (
    <>
      <PageHero overline="Оборудование в аренду" title={<>Всё необходимое для <span className="text-accent">незабываемого события</span></>} text="Не просто прокат вещей — мы создаём полноценную инфраструктуру вашего события: декор, конструкции и техническое оснащение в одной смете.">
        <Btn onClick={() => openLead("Аренда")} className="mt-8">Оставить заявку</Btn>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-5 lg:grid-cols-2">
          {rental.map((r, i) => (
            <Reveal key={r.title} delay={i * 0.08}>
              <div className="card-hover overflow-hidden rounded-3xl border border-line bg-card">
                <img src={r.image} alt="" loading="lazy" className="h-56 w-full object-cover" />
                <div className="p-7">
                  <h2 className="display-h text-2xl font-bold">{r.title}</h2>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {r.items.map((it) => (
                      <span key={it} className="rounded-xl border border-line bg-bg2 px-3.5 py-2 text-sm text-ink/80">{it}</span>
                    ))}
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-24">
        <SectionHead overline="Как заказать" title="5 шагов до готовой площадки" />
        <div className="grid gap-4 md:grid-cols-5">
          {rentalSteps.map((s, i) => (
            <Reveal key={s.n} delay={i * 0.06}>
              <div className="relative h-full rounded-2xl border border-line bg-card p-5">
                <span className="font-display text-xs font-black text-accent">{s.n}</span>
                <h3 className="mt-3 font-display text-base font-bold">{s.t}</h3>
                <p className="mt-2 text-xs leading-relaxed text-mut">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-5 pb-10">
        <SectionHead overline="FAQ" title="Частые вопросы об аренде" />
        <Accordion items={rentalFaq} />
      </section>
    </>
  );
}
