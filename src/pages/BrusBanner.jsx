import { Link } from "react-router-dom";
import { usePageMeta } from "../hooks/usePageMeta";
import { useUI } from "../lib/store";
import { fmtMoney } from "../lib/format";
import { Btn, SectionHead } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { Check, Clock, Spark } from "../components/ui/Icons";
import Gallery from "../components/ui/Gallery";
import { CtaBand, FaqBlock, ProcessSteps, RelatedLinks } from "../components/blocks/ServiceSections";
import {
  brusHero, brusBenefits, brusCompare, brusSpecs, brusVariants, brusSizes,
  brusIncluded, brusGallery, brusProcess, brusFaq, brusRelated, brusScopes,
} from "../data/brusBanner";

export default function BrusBanner() {
  const { openLead } = useUI();
  usePageMeta(
    "Брус-баннер на скрытом каркасе — изготовление и монтаж в Москве и СПб | SM-Production",
    "Пресс-воллы и брус-баннеры на скрытом деревянном каркасе: ровное полотно без складок и труб, любая форма, изготовление от 24 часов. Цены от 16 500 ₽, монтаж по Москве и СПб."
  );

  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden pt-36 md:pt-44">
        <div className="grid-bg mask-fade-b absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="pointer-events-none absolute -top-32 right-[-8%] h-[460px] w-[460px] rounded-full bg-accent/15 blur-[130px]" aria-hidden="true" />
        <div className="relative mx-auto max-w-7xl px-5">
          <nav className="mb-6 text-xs text-mut" aria-label="Хлебные крошки">
            <Link to="/" className="hover:text-ink">Главная</Link> / <Link to="/uslugi" className="hover:text-ink">Услуги</Link> / <span className="text-ink">Брус-баннер</span>
          </nav>
          <div className="grid items-end gap-10 lg:grid-cols-[1.15fr_1fr]">
            <Reveal>
              <p className="font-display text-xs uppercase tracking-[0.3em] text-accent">{brusHero.overline}</p>
              <h1 className="display-h mt-4 text-4xl font-black md:text-6xl">
                {brusHero.title} <span className="text-accent">{brusHero.subtitle}</span>
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-relaxed text-mut">{brusHero.lead}</p>
              <div className="mt-7 flex flex-wrap gap-2">
                {brusHero.badges.map((b) => (
                  <span key={b} className="inline-flex items-center gap-2 rounded-full border border-line px-3.5 py-2 text-xs font-semibold text-mut">
                    <Check size={12} className="text-acid" /> {b}
                  </span>
                ))}
              </div>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Btn onClick={() => openLead("Брус-баннер")}>
                  Рассчитать стоимость <span className="opacity-70">от {fmtMoney(brusHero.priceFrom)}</span>
                </Btn>
                <Btn to="/portfolio" variant="ghost">Смотреть кейсы</Btn>
              </div>
            </Reveal>
            <Reveal delay={0.15}>
              <div className="img-zoom overflow-hidden rounded-3xl border border-line">
                <img src={brusHero.image} alt="Пресс-волл на скрытом деревянном каркасе" className="h-72 w-full object-cover lg:h-[420px]" />
              </div>
            </Reveal>
          </div>

          <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["24 ч", "изготовление при готовом макете"],
              ["1440 dpi", "печать и матовая ламинация"],
              ["20–40 см", "глубина запечатанного торца"],
              ["−40%", "бюджет при повторной печати"],
            ].map(([v, d], i) => (
              <Reveal key={v} delay={i * 0.06}>
                <div className="rounded-2xl border border-line bg-card/70 px-5 py-4">
                  <p className="display-h text-2xl font-black text-accent">{v}</p>
                  <p className="mt-1 text-xs leading-relaxed text-mut">{d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <SectionHead overline="Преимущества" title={<>Почему брус-баннер выглядит <span className="text-accent">дороже</span></>} text="Конструкция, в которой нет ни одной видимой детали каркаса: гости видят только вашу рекламу, а камера — ровное матовое полотно." />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {brusBenefits.map((b, i) => (
            <Reveal key={b.t} delay={(i % 3) * 0.07}>
              <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                <span className="inline-flex rounded-2xl bg-accent/12 p-3 text-accent"><Spark size={18} /></span>
                <h3 className="mt-5 font-display text-lg font-bold">{b.t}</h3>
                <p className="mt-3 text-sm leading-relaxed text-mut">{b.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* COMPARE */}
      <section className="border-y border-line bg-bg2 py-20 md:py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Сравнение" title={brusCompare.title} text={brusCompare.text} />
          <div className="overflow-hidden rounded-3xl border border-line bg-card">
            <div className="hidden grid-cols-[0.8fr_1fr_1fr] gap-4 border-b border-line px-6 py-4 font-display text-[10px] uppercase tracking-[0.2em] text-mut md:grid">
              <span>Параметр</span><span>Баннер на «Джокере»</span><span className="text-accent">Брус-баннер SM</span>
            </div>
            {brusCompare.rows.map(([k, a, b]) => (
              <div key={k} className="grid gap-2 border-b border-line px-6 py-5 last:border-0 md:grid-cols-[0.8fr_1fr_1fr] md:items-center md:gap-4">
                <span className="font-display text-sm font-bold">{k}</span>
                <span className="text-sm text-mut">— {a}</span>
                <span className="flex items-start gap-2 text-sm font-medium">
                  <Check size={15} className="mt-0.5 shrink-0 text-acid" />{b}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SCOPES */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <SectionHead overline="Применение" title={<>Где работает <span className="text-accent">брус-баннер</span></>} text="Одна технология закрывает пресс-волл, фон сцены, регистрацию, стенд и арт-объекты — оформление собирается в единую картинку." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {brusScopes.map((s, i) => (
            <Reveal key={s.t} delay={(i % 3) * 0.06}>
              <div className="relative h-full rounded-3xl border border-line bg-card p-6">
                {s.tag && (
                  <span className="absolute right-5 top-5 rounded-full bg-accent px-2.5 py-1 font-display text-[9px] uppercase tracking-widest text-white">{s.tag}</span>
                )}
                <h3 className="font-display text-base font-bold">{s.t}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-mut">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* GALLERY */}
      <section className="border-y border-line bg-bg2 py-20 md:py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Работы" title="Как это выглядит на площадке" text="Визуализации типовых конфигураций: пресс-воллы, фигурные и угловые конструкции, брус-колонны. Нажмите на карточку, чтобы открыть просмотр." />
          <Gallery items={brusGallery} />
        </div>
      </section>

      {/* SPECS + VARIANTS */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
          <Reveal>
            <SectionHead overline="Технические данные" title="Из чего собрана конструкция" className="mb-8" />
            <dl className="overflow-hidden rounded-3xl border border-line">
              {brusSpecs.map(([k, v], i) => (
                <div key={k} className={`grid gap-1 px-6 py-4 sm:grid-cols-[0.9fr_1.3fr] sm:gap-4 ${i % 2 ? "bg-card" : "bg-bg2"}`}>
                  <dt className="font-display text-xs uppercase tracking-[0.16em] text-mut">{k}</dt>
                  <dd className="text-sm font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </Reveal>
          <Reveal delay={0.1}>
            <SectionHead overline="Исполнения" title="Варианты под задачу" className="mb-8" />
            <div className="grid gap-3 sm:grid-cols-2">
              {brusVariants.map((v) => (
                <div key={v.t} className="rounded-2xl border border-line bg-card p-5">
                  <p className="font-display text-sm font-bold">{v.t}</p>
                  <p className="mt-2 text-xs leading-relaxed text-mut">{v.d}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* PRICES */}
      <section id="ceny" className="border-y border-line bg-bg2 py-20 md:py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Цены" title="Стандартные размеры и стоимость" text="Цены розничные, указаны «от». Точная смета зависит от макета, материала полотна, запечатки торцов и условий монтажа на площадке." />
          <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
            <div className="overflow-hidden rounded-3xl border border-line bg-card">
              <div className="grid grid-cols-[1fr_1fr] gap-3 border-b border-line px-5 py-4 font-display text-[10px] uppercase tracking-[0.16em] text-mut sm:grid-cols-[0.9fr_1fr_1fr] sm:px-7">
                <span>Размер</span><span className="hidden sm:block">Изготовление</span><span>С монтажом</span>
              </div>
              {brusSizes.map((s) => (
                <div key={s.size} className="grid grid-cols-[1fr_1fr] items-center gap-3 border-b border-line px-5 py-4 last:border-0 sm:grid-cols-[0.9fr_1fr_1fr] sm:px-7">
                  <span className="font-display text-sm font-bold">{s.size}</span>
                  <span className="hidden text-sm text-mut sm:block">от {fmtMoney(s.made)}</span>
                  <span className="text-sm font-bold text-accent">от {fmtMoney(s.turnkey)}</span>
                  <span className="col-span-2 -mt-1 text-[11px] text-mut sm:hidden">изготовление от {fmtMoney(s.made)}</span>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-4">
              <div className="rounded-3xl border border-line bg-card p-6">
                <h3 className="font-display text-sm uppercase tracking-[0.2em] text-mut">В стоимость входит</h3>
                <ul className="mt-4 space-y-2.5">
                  {brusIncluded.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm">
                      <span className="mt-0.5 rounded-full bg-acid/15 p-1 text-acid"><Check size={11} /></span>{f}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-3xl border border-accent/60 bg-accent/10 p-6">
                <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.22em] text-accent"><Spark size={13} /> Акция</p>
                <p className="mt-2 text-sm font-medium leading-relaxed">При заказе брус-баннера до конца месяца — доставка по Москве или Санкт-Петербургу бесплатно.</p>
              </div>
              <div className="rounded-3xl border border-line bg-card p-6">
                <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.22em] text-mut"><Clock size={13} className="text-accent" /> Нестандартный размер</p>
                <p className="mt-2 text-sm text-mut">Высота до 5 м, любая ширина, фигурная геометрия — считаем индивидуально по чертежу за 1 час.</p>
                <button onClick={() => openLead("Брус-баннер: нестандарт")} className="mt-4 font-display text-sm uppercase tracking-[0.14em] text-accent link-underline">Запросить расчёт</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ProcessSteps items={brusProcess} title={<>От заявки до демонтажа — <span className="text-accent">шесть шагов</span></>} text="Коммерческое предложение — за час, макет — в тот же день, конструкция на площадке — от 24 часов." />

      <FaqBlock items={brusFaq} title={<>Брус-баннер: <span className="text-accent">вопросы и ответы</span></>} />

      <RelatedLinks items={brusRelated} />

      <CtaBand
        topic="Брус-баннер: расчёт"
        title="Посчитаем брус-баннер под ваше мероприятие"
        text="Пришлите размер, площадку и дату — вернёмся со сметой и эскизом в тот же день. Если макет уже есть, проверим вылеты и разрешение бесплатно."
        note="Позвонить: +7 (495) 799-00-19 · Telegram: @sm_production"
      />
    </>
  );
}
