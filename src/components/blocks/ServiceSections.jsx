import { Link } from "react-router-dom";
import { Accordion, Btn, SectionHead } from "../ui/bits";
import { Reveal } from "../ui/motion";
import { ArrowUpRight, Check, Clock, MapPin } from "../ui/Icons";
import { useUI } from "../../lib/store";

/** Таймлайн этапов работы — нумерация, прогресс-линия по скроллу не нужна, работает в связке с Reveal */
export function ProcessSteps({ items, overline = "Как мы работаем", title, text }) {
  return (
    <section className="mx-auto max-w-7xl px-5 py-20">
      <SectionHead overline={overline} title={title} text={text} />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map(([t, d], i) => (
          <Reveal key={t} delay={(i % 3) * 0.07}>
            <div className="group relative h-full overflow-hidden rounded-3xl border border-line bg-card p-7 transition-colors hover:border-accent">
              <span className="text-outline display-h text-4xl font-black transition-all group-hover:text-accent group-hover:[-webkit-text-stroke:0px]">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-5 font-display text-lg font-bold">{t}</h3>
              <p className="mt-3 text-sm leading-relaxed text-mut">{d}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/** Блок FAQ по услуге */
export function FaqBlock({ items, title = "Частые вопросы", overline = "FAQ", text }) {
  const { openLead } = useUI();
  return (
    <section className="mx-auto max-w-5xl px-5 py-20">
      <SectionHead overline={overline} title={title} text={text} />
      <Accordion items={items} />
      <div className="mt-10 flex flex-wrap items-center gap-4 rounded-3xl border border-line bg-card p-7">
        <div className="flex-1">
          <p className="font-display text-lg font-bold">Не нашли свой вопрос?</p>
          <p className="mt-1.5 text-sm text-mut">Ответим в течение рабочего дня, а по срочным проектам — в течение часа.</p>
        </div>
        <Btn onClick={() => openLead(title)}>Задать вопрос</Btn>
      </div>
    </section>
  );
}

/** Список связанных услуг / материалов */
export function RelatedLinks({ items, title = "Рядом по теме" }) {
  return (
    <section className="mx-auto max-w-7xl px-5 pb-16">
      <h2 className="display-h mb-8 text-2xl font-bold md:text-3xl">{title}</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((r) => (
          <Link key={r.to} to={r.to} className="card-hover group flex h-full flex-col rounded-2xl border border-line bg-card p-6">
            <div className="flex items-start justify-between gap-3">
              <p className="font-display text-base font-bold group-hover:text-accent">{r.t}</p>
              <ArrowUpRight size={16} className="mt-1 shrink-0 text-mut transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent" />
            </div>
            <p className="mt-2 text-sm leading-relaxed text-mut">{r.d}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

/** Финальный CTA-баннер: заявка + контактные факты */
export function CtaBand({ title, text, topic, note }) {
  const { openLead } = useUI();
  return (
    <section className="mx-auto max-w-7xl px-5 pb-20">
      <div className="relative overflow-hidden rounded-3xl border border-line bg-bg2 p-8 md:p-12">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/20 blur-[110px]" aria-hidden="true" />
        <div className="relative grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-center">
          <div>
            <h2 className="display-h text-3xl font-bold md:text-4xl">{title}</h2>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-mut">{text}</p>
            <div className="mt-7 flex flex-wrap gap-4">
              <Btn onClick={() => openLead(topic)}>Оставить заявку</Btn>
              <Btn to="/kontakty" variant="ghost">Контакты и адреса</Btn>
            </div>
            {note && <p className="mt-4 text-xs text-mut">{note}</p>}
          </div>
          <ul className="space-y-3 text-sm text-mut">
            {[
              [<Clock size={15} />, "КП и смета — за 1 час, ответ на запрос в тот же день"],
              [<MapPin size={15} />, "Москва: Остаповский проезд, 9 ст13 · СПб: ул. Швецова, 41"],
              [<Check size={15} />, "Договор, счёт и закрывающие документы для бухгалтерии"],
            ].map(([icon, txt], i) => (
              <li key={i} className="flex items-start gap-3 rounded-2xl border border-line bg-card px-5 py-4">
                <span className="mt-0.5 text-accent">{icon}</span>
                <span>{txt}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
