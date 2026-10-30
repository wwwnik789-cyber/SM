import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import { useUI } from "../lib/store";
import { fmtMoney } from "../lib/format";
import { Btn, SectionHead } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Check, Clock, Factory, MapPin, Spark } from "../components/ui/Icons";
import Gallery from "../components/ui/Gallery";
import { CtaBand, FaqBlock, ProcessSteps, RelatedLinks } from "../components/blocks/ServiceSections";
import {
  receptionHero, receptionProblem, receptionServices, receptionBenefits,
  receptionProcess, receptionPrices, receptionGallery, receptionFaq, receptionRelated,
} from "../data/reception";

export default function Reception() {
  const { openLead } = useUI();
  usePageMeta(
    "Брендирование офисов и зон ресепшн под ключ — Москва и СПб | SM-Production",
    "Стойки ресепшн по индивидуальному дизайну, объёмные логотипы, навигация и интерьерная графика для офисов и шоурумов. Собственное производство, бесплатный замер, 3D-визуализация, гарантия 1 год."
  );

  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden pt-36 md:pt-44">
        <div className="grid-bg mask-fade-b absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="pointer-events-none absolute -top-32 right-[-8%] h-[460px] w-[460px] rounded-full bg-acid/12 blur-[130px]" aria-hidden="true" />
        <div className="relative mx-auto max-w-7xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/uslugi" className="hover:text-ink">Услуги</Link> / <span className="text-ink">Брендирование офисов</span>
          </nav>
          <div className="grid items-end gap-10 lg:grid-cols-[1.15fr_1fr]">
            <Reveal>
              <p className="flex items-center gap-2 font-display text-xs uppercase tracking-[0.3em] text-accent">
                <Spark size={13} /> {receptionHero.overline}
              </p>
              <h1 className="display-h mt-4 text-4xl font-black md:text-6xl">
                {receptionHero.title} <span className="text-accent">{receptionHero.subtitle}</span>
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-relaxed text-mut">{receptionHero.lead}</p>
              <div className="mt-7 flex flex-wrap gap-2">
                {receptionHero.badges.map((b) => (
                  <span key={b} className="inline-flex items-center gap-2 rounded-full border border-line px-3.5 py-2 text-xs font-semibold text-mut">
                    <Check size={12} className="text-acid" /> {b}
                  </span>
                ))}
              </div>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Btn onClick={() => openLead("Брендирование офиса")}>
                  Вызвать замерщика <span className="opacity-70">от {fmtMoney(receptionHero.priceFrom)}</span>
                </Btn>
                <Btn to="/portfolio" variant="ghost">Примеры работ</Btn>
              </div>
            </Reveal>
            <Reveal delay={0.15}>
              <div className="img-zoom overflow-hidden rounded-3xl border border-line">
                <img src={receptionHero.image} alt="Зона ресепшн с объёмным логотипом на стене" className="h-72 w-full object-cover lg:h-[420px]" />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* PROBLEM / POSITIONING */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[1.3fr_1fr] lg:items-start">
          <Reveal>
            <SectionHead overline="Задача" title={receptionProblem.title} className="mb-6" />
            <div className="space-y-5 text-lg leading-relaxed text-ink/85">
              {receptionProblem.paragraphs.map((p) => <p key={p}>{p}</p>)}
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="grid gap-3">
              {receptionProblem.stats.map(([v, d]) => (
                <div key={v} className="rounded-3xl border border-line bg-card px-6 py-5">
                  <p className="display-h text-3xl font-black text-accent">{v}</p>
                  <p className="mt-1 text-sm text-mut">{d}</p>
                </div>
              ))}
              <div className="rounded-3xl border border-line bg-bg2 px-6 py-5 text-sm text-mut">
                <span className="flex items-center gap-2 font-display text-xs uppercase tracking-[0.2em] text-ink"><Factory size={14} className="text-accent" /> Свой цех 750 м²</span>
                <p className="mt-2">Москва и Санкт-Петербург: производство, склад и монтажные бригады в двух городах.</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* SERVICES BENTO */}
      <section className="border-y border-line bg-bg2 py-20 md:py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Что делаем" title={<>Какие задачи <span className="text-accent">закрываем</span></>} text="Полный перечень элементов фирменного стиля в интерьере — можно заказать по отдельности или комплексом под ключ." />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {receptionServices.map((s, i) => (
              <Reveal key={s.t} delay={(i % 3) * 0.06} className={i === 0 ? "sm:col-span-2" : ""}>
                <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                  <span className="font-display text-[10px] uppercase tracking-[0.24em] text-accent">{String(i + 1).padStart(2, "0")}</span>
                  <h3 className={`mt-3 font-display font-bold ${i === 0 ? "text-xl" : "text-base"}`}>{s.t}</h3>
                  <p className="mt-2.5 text-sm leading-relaxed text-mut">{s.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <SectionHead overline="Преимущества" title={<>Почему заказывают <span className="text-accent">у нас</span></>} text="Собственный цех, фиксированная смета и монтаж в нерабочие часы — офис продолжает работать, пока мы делаем пространство." />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {receptionBenefits.map((b, i) => (
            <Reveal key={b.t} delay={(i % 3) * 0.06}>
              <div className="h-full rounded-3xl border border-line bg-card p-6">
                <span className="inline-flex rounded-2xl bg-acid/12 p-2.5 text-acid"><Check size={16} /></span>
                <h3 className="mt-4 font-display text-base font-bold">{b.t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-mut">{b.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* GALLERY */}
      <section className="border-y border-line bg-bg2 py-20 md:py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Визуализации" title="Зоны ресепшн и брендированные интерьеры" text="Концепты, которые показываем на согласовании до старта производства. Нажмите на карточку, чтобы открыть просмотр." />
          <Gallery items={receptionGallery} />
        </div>
      </section>

      {/* PRICES */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <SectionHead overline="Цены" title="Ориентиры по стоимости" text="Стоимость фиксируется в КП после замера и согласования 3D-визуализации и не меняется в процессе работ." />
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-start">
          <div className="overflow-hidden rounded-3xl border border-line bg-card">
            {receptionPrices.map((p, i) => (
              <div key={p.t} className={`flex flex-col gap-1.5 px-6 py-5 sm:flex-row sm:items-center sm:justify-between sm:gap-6 ${i % 2 ? "bg-bg2" : ""}`}>
                <span className="text-sm font-medium">{p.t}</span>
                <span className="shrink-0 font-display text-sm font-bold text-accent">{p.price}</span>
              </div>
            ))}
          </div>
          <div className="flex flex-col gap-4">
            <div className="rounded-3xl border border-accent/60 bg-accent/10 p-6">
              <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.22em] text-accent"><Spark size={13} /> Для первых клиентов</p>
              <p className="mt-2 text-sm font-medium leading-relaxed">Бесплатный выезд замерщика в пределах МКАД / КАД и 3D-визуализация при заказе производства.</p>
            </div>
            <div className="rounded-3xl border border-line bg-card p-6">
              <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.22em] text-mut"><Clock size={13} className="text-accent" /> Монтаж без остановки офиса</p>
              <p className="mt-2 text-sm text-mut">Работаем вечером, ночью и в выходные. Допуск и пропуска в бизнес-центр согласуем сами.</p>
            </div>
            <div className="rounded-3xl border border-line bg-card p-6">
              <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.22em] text-mut"><MapPin size={13} className="text-accent" /> Москва, СПб и регионы</p>
              <p className="mt-2 text-sm text-mut">Изготавливаем в двух городах и отправляем конструкции транспортной компанией в регионы.</p>
            </div>
          </div>
        </div>
      </section>

      <ProcessSteps
        items={receptionProcess}
        title={<>От замера до сдачи объекта — <span className="text-accent">шесть шагов</span></>}
        text="Смета после замера, 3D до старта производства, фотоотчёты на каждом этапе и гарантия год после сдачи."
      />

      <FaqBlock items={receptionFaq} title={<>Брендирование офиса: <span className="text-accent">вопросы и ответы</span></>} />

      <RelatedLinks items={receptionRelated} />

      <CtaBand
        topic="Брендирование офиса: замер"
        title="Обсудим брендирование вашего офиса или ресепшн"
        text="Пришлите план помещения, фотографии зоны или референсы — предложим концепцию, состав элементов и смету. Замер бесплатный."
        note="Позвонить: +7 (495) 799-00-19 · Telegram: @sm_production"
      />
    </>
  );
}
