import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Counter, Reveal } from "../components/ui/motion";
import { Accordion, Btn, SectionHead } from "../components/ui/bits";
import {
  ArrowUpRight, Bolt, Check, Clock, Cube, Factory, Mail, MapPin, Phone, Ruler, Send, Spark,
} from "../components/ui/Icons";
import { EMAIL, PHONE, PHONE_HREF, TG } from "../lib/format";
import { useUI } from "../lib/store";

const ADDRESS = "109316, Москва, Остаповский проезд, д. 9, с. 13";
const HOURS = "Работаем 24/7 · производство ежедневно 9:00–22:00";
const MAP = "https://yandex.ru/maps/?ll=37.714032%2C55.722381&z=16";
const MAP_ORG = "https://yandex.ru/maps/org/sm_production/135757112868";
const TG_HANDLE = "@sm_production_sm";

const channels = [
  {
    icon: <Phone size={20} />,
    label: "Телефон",
    value: PHONE,
    href: PHONE_HREF,
    note: "Звонок или сообщение — как удобнее. Отвечаем круглосуточно.",
  },
  {
    icon: <Mail size={20} />,
    label: "Почта",
    value: EMAIL,
    href: `mailto:${EMAIL}`,
    note: "Пришлите бриф, макет или фото площадки — ответим со сметой и сроком.",
  },
  {
    icon: <Send size={20} />,
    label: "Telegram",
    value: TG_HANDLE,
    href: TG,
    note: "Быстрые вопросы, эскизы и правки в одном чате.",
  },
];

const stats = [
  { value: 6, suffix: "", label: "участков в одном цеху" },
  { value: 3, suffix: " ч", label: "минимальный срок печати баннера" },
  { value: 24, suffix: "/7", label: "монтажи и поддержка" },
  { value: 300, suffix: "+", label: "реализованных проектов" },
];

const equipment = [
  { icon: <Factory size={18} />, title: "УФ-печать и широкоформат", text: "Баннер, плёнка, композит, ПВХ. Печать на своих материалах, без посредников." },
  { icon: <Ruler size={18} />, title: "ЧПУ-фрезеровка и гравировка", text: "Криволинейные формы, буквы, пазы и присадка — по вектору, а не по шаблону." },
  { icon: <Cube size={18} />, title: "Поклейка и ламинация", text: "Монтаж плёнки на плоскость и объём, запечатка торцов, матовые покрытия." },
  { icon: <Bolt size={18} />, title: "Сварка каркасов", text: "Металл для сцен, стендов и световых конструкций: прочность считаем под нагрузку." },
  { icon: <Spark size={18} />, title: "Зона сборки и тестирования", text: "Собираем конструкцию целиком до выезда: проверяем стыки, свет и крепёж." },
  { icon: <Check size={18} />, title: "Склад и логистика", text: "Храним каркасы между событиями и отгружаем на площадку в монтажное окно." },
];

const visitSteps = [
  { n: "01", t: "Напишите или позвоните", d: "Скажите, что хотите посмотреть, и когда вам удобно — включая вечер и монтажную ночь." },
  { n: "02", t: "Согласуем время", d: "Подберём окно, когда нужный участок свободен и можно показать его в работе, а не на паузе." },
  { n: "03", t: "Встречаем на проходной", d: "Проведём по цеху, покажем материалы и вашу конструкцию до отправки на площадку." },
];

const faq = [
  {
    q: "Можно ли приехать без записи?",
    a: "Лучше записаться. Мы согласуем время так, чтобы вы застали нужный участок в работе, а не на паузе, и кто-то из производства смог провести вас по цеху и ответить на вопросы.",
  },
  {
    q: "Правда ли, что можно приехать ночью?",
    a: "Да, если это согласовано заранее. Монтажи идут круглосуточно, и перед ночным заездом часто нужно посмотреть конструкцию вживую. Напишите — подберём время.",
  },
  {
    q: "Можно забрать конструкцию самому?",
    a: "Да. Отгрузка идёт со склада по адресу производства: упакуем, поможем с погрузкой и отдадим документы. Если нужна доставка — организуем.",
  },
  {
    q: "Покажете материалы до печати?",
    a: "Покажем образцы плёнок, баннера, акрила и композита, объясним, что и где держится лучше, и предложим варианты под ваш бюджет — без сюрпризов после запуска тиража.",
  },
];

export default function Contacts() {
  usePageMeta(
    "Контакты SM Production — Москва, производство на Остаповском проезде",
    "Телефон, почта, мессенджеры и адрес производства SM-Production в Москве. Приезжайте в цех: покажем станки, материалы и вашу конструкцию до отправки на площадку.",
  );
  const { openLead } = useUI();

  return (
    <>
      <PageHero
        overline="Контакты"
        title={<>Приезжайте в цех — <span className="text-accent">покажем, как делается ваш проект</span></>}
        text="Один адрес, один телефон и живые люди на связи круглосуточно. Производство в Москве на Остаповском проезде: здесь печатаем, фрезеруем, варим и собираем конструкции до отправки на площадку."
      >
        <div className="mt-8 flex flex-wrap gap-3">
          <a href={PHONE_HREF} className="btn-sheen inline-flex items-center gap-2 rounded-xl bg-accent px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] text-white">
            <Phone size={15} /> {PHONE}
          </a>
          <a href={`mailto:${EMAIL}`} className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent">
            <Mail size={15} /> {EMAIL}
          </a>
          <a href={TG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent">
            <Send size={15} /> Telegram
          </a>
        </div>
        <div className="mt-7 flex flex-wrap items-center gap-x-7 gap-y-3 text-sm text-mut">
          <span className="inline-flex items-center gap-2"><span className="animate-pulse-dot h-2 w-2 rounded-full bg-acid" /> На связи прямо сейчас</span>
          <span className="inline-flex items-center gap-2"><Clock size={14} className="text-accent" /> {HOURS}</span>
        </div>
      </PageHero>

      {/* ---------- каналы связи ---------- */}
      <section className="mx-auto max-w-7xl px-5 pb-6">
        <div className="grid gap-4 md:grid-cols-3">
          {channels.map((c, i) => (
            <Reveal key={c.label} delay={i * 0.07}>
              <a
                href={c.href}
                target={c.href.startsWith("http") ? "_blank" : undefined}
                rel="noreferrer"
                className="card-hover group flex h-full flex-col rounded-3xl border border-line bg-card p-7"
              >
                <div className="flex items-start justify-between">
                  <span className="rounded-2xl bg-accent/12 p-3 text-accent">{c.icon}</span>
                  <ArrowUpRight size={18} className="text-mut transition-all duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent" />
                </div>
                <p className="mt-6 font-display text-[10px] uppercase tracking-[0.28em] text-mut">{c.label}</p>
                <p className="mt-2 display-h break-words text-xl font-bold group-hover:text-accent">{c.value}</p>
                <p className="mt-3 text-sm leading-relaxed text-mut">{c.note}</p>
              </a>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ---------- адрес производства ---------- */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <Reveal>
          <div className="overflow-hidden rounded-[28px] border border-line bg-card">
            <div className="grid lg:grid-cols-[1.05fr_1fr]">
              <div className="relative p-8 md:p-11">
                <div className="grid-bg pointer-events-none absolute inset-0 opacity-30" aria-hidden="true" />
                <div className="relative">
                  <div className="mb-4 flex items-center gap-3">
                    <span className="h-2 w-2 rotate-45 bg-accent" />
                    <span className="font-display text-xs uppercase tracking-[0.28em] text-mut">Производство и офис · Москва</span>
                  </div>
                  <h2 className="display-h max-w-md text-3xl font-bold md:text-4xl">Наш адрес в Москве</h2>

                  <div className="mt-8 space-y-5">
                    <p className="flex items-start gap-3 text-ink/85">
                      <MapPin size={18} className="mt-0.5 shrink-0 text-accent" />
                      <span>{ADDRESS}</span>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Clock size={18} className="mt-0.5 shrink-0 text-accent" />
                      <span>{HOURS}</span>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Phone size={18} className="mt-0.5 shrink-0 text-accent" />
                      <a href={PHONE_HREF} className="link-underline font-display text-base font-bold text-ink">{PHONE}</a>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Mail size={18} className="mt-0.5 shrink-0 text-accent" />
                      <a href={`mailto:${EMAIL}`} className="link-underline text-ink/85">{EMAIL}</a>
                    </p>
                  </div>

                  <div className="mt-9 flex flex-wrap gap-3">
                    <a href={MAP} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-5 py-3 text-sm font-semibold transition-colors hover:border-accent hover:text-accent">
                      Построить маршрут <ArrowUpRight size={14} />
                    </a>
                    <button onClick={() => openLead("Визит на производство")} className="inline-flex items-center gap-2 rounded-xl border border-line px-5 py-3 text-sm font-semibold transition-colors hover:border-accent hover:text-accent">
                      Записаться на визит
                    </button>
                  </div>
                  <p className="mt-5 text-xs text-mut">Визит — по предварительной записи: так вас встретят и проведут по цеху.</p>
                </div>
              </div>

              <div className="relative min-h-[320px] border-t border-line lg:border-l lg:border-t-0">
                <img src="/media/workshop.jpg" alt="Производственный цех SM-Production" loading="lazy" className="absolute inset-0 h-full w-full object-cover opacity-60" />
                <div className="absolute inset-0 bg-gradient-to-tr from-black/85 via-black/45 to-black/10" />
                <div className="relative flex h-full flex-col justify-between p-8 md:p-10">
                  <div className="flex justify-end">
                    <a href={MAP_ORG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-black/30 px-4 py-2 text-xs font-semibold text-white/90 backdrop-blur transition-colors hover:border-acid hover:text-acid">
                      Карточка в Яндекс Картах <ArrowUpRight size={13} />
                    </a>
                  </div>
                  <div>
                    <p className="font-display text-[10px] uppercase tracking-[0.3em] text-acid">Свой цех</p>
                    <p className="mt-3 max-w-xs text-sm leading-relaxed text-white/80">
                      ЧПУ-фрезер, УФ-принтер, сварка и зона сборки в одном контуре. Конструкцию собирают целиком до выезда на площадку.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ---------- производство ---------- */}
      <section className="border-y border-line bg-bg2 py-20">
        <div className="mx-auto max-w-7xl px-5">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:items-end">
            <SectionHead
              overline="Производство"
              title={<>Цех, в который <span className="text-accent">можно приехать</span></>}
              text="Полный цикл в одном контуре: от файла до готовой конструкции. Печать, фрезеровка, поклейка, сварка и сборка — на своей площадке, поэтому сроки не зависят от подрядчиков."
            />
            <div className="grid grid-cols-2 gap-4 lg:mb-1">
              {stats.map((s, i) => (
                <Reveal key={s.label} delay={i * 0.06}>
                  <div className="rounded-2xl border border-line bg-card px-4 py-5 text-center">
                    <p className="display-h text-2xl font-black text-accent"><Counter value={s.value} suffix={s.suffix} /></p>
                    <p className="mt-2 text-[11px] leading-snug text-mut">{s.label}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-[1.4fr_1fr]">
            <Reveal>
              <figure className="img-zoom group relative h-full min-h-[320px] overflow-hidden rounded-3xl border border-line">
                <img src="/media/workshop.jpg" alt="Цех: ЧПУ-фрезер и рулоны баннера на стеллажах" loading="lazy" className="h-full w-full object-cover" />
                <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-6 text-sm text-white/85">
                  Раскрой и фрезеровка: детали режутся по вектору, поэтому сложная форма не превращается в «примерно такую же».
                </figcaption>
              </figure>
            </Reveal>
            <div className="grid gap-5">
              <Reveal delay={0.08}>
                <figure className="img-zoom relative overflow-hidden rounded-3xl border border-line">
                  <img src="/media/design-production.jpg" alt="УФ-принтер в работе" loading="lazy" className="h-52 w-full object-cover" />
                  <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-5 text-xs text-white/80">
                    УФ-печать: баннер 3 × 6 м уходит в работу в день утверждения макета.
                  </figcaption>
                </figure>
              </Reveal>
              <Reveal delay={0.14}>
                <figure className="img-zoom relative overflow-hidden rounded-3xl border border-line">
                  <img src="/media/studio.jpg" alt="Съёмочная студия SM-Media" loading="lazy" className="h-52 w-full object-cover" />
                  <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-5 text-xs text-white/80">
                    SM-Media: студия и выездная съёмка в одном контуре с производством.
                  </figcaption>
                </figure>
              </Reveal>
            </div>
          </div>

          {/* что увидите на визите */}
          <Reveal delay={0.06}>
            <div className="mt-5 rounded-3xl border border-line bg-card p-7 md:p-8">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <h3 className="display-h text-xl font-bold">Что увидите на визите</h3>
                <p className="text-sm text-mut">Без записи не проведём — производство действующее.</p>
              </div>
              <ul className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  "Станки в работе, а не на фото",
                  "Образцы плёнок, баннера, акрила и композита",
                  "Свою конструкцию до отправки на площадку",
                  "Как считается срок и что влияет на смету",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2.5 text-sm text-ink/85">
                    <Check size={16} className="mt-0.5 shrink-0 text-acid" /> {t}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

          <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {equipment.map((e, i) => (
              <Reveal key={e.title} delay={(i % 3) * 0.06}>
                <div className="card-hover flex h-full gap-4 rounded-2xl border border-line bg-card p-6">
                  <span className="h-fit rounded-xl bg-accent/12 p-2.5 text-accent">{e.icon}</span>
                  <div>
                    <h3 className="font-display text-sm font-bold">{e.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-mut">{e.text}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>

          <Reveal delay={0.1}>
            <div className="mt-8 flex flex-col items-start justify-between gap-5 rounded-3xl border border-line bg-card p-7 md:flex-row md:items-center">
              <div>
                <h3 className="display-h text-xl font-bold">Хотите увидеть цех своими глазами?</h3>
                <p className="mt-2 max-w-xl text-sm text-mut">Проведём по участкам, покажем материалы и объясним, из чего складывается цена и срок вашего проекта.</p>
              </div>
              <Btn onClick={() => openLead("Визит на производство")}>Записаться на визит</Btn>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ---------- как попасть ---------- */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <SectionHead
          overline="Визит"
          title="Как попасть в цех"
          text="Производство действующее, поэтому просто так по территории не пройти: нужен пропуск. Зато и увидеть можно всё по-настоящему."
        />
        <div className="grid gap-4 md:grid-cols-3">
          {visitSteps.map((s, i) => (
            <Reveal key={s.n} delay={i * 0.07}>
              <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                <p className="display-h text-4xl font-black text-outline-accent">{s.n}</p>
                <h3 className="mt-4 font-display text-lg font-bold">{s.t}</h3>
                <p className="mt-3 text-sm leading-relaxed text-mut">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ---------- вопросы ---------- */}
      <section className="mx-auto max-w-4xl px-5 pb-16">
        <SectionHead overline="Детали" title="Частые вопросы о визите" />
        <Accordion items={faq} />
      </section>

      {/* ---------- финал ---------- */}
      <section className="mx-auto max-w-7xl px-5 pb-6">
        <Reveal>
          <div className="relative overflow-hidden rounded-[28px] border border-line bg-card p-9 md:p-12">
            <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/15 blur-[110px]" aria-hidden="true" />
            <div className="relative flex flex-col items-start justify-between gap-7 md:flex-row md:items-center">
              <div>
                <h2 className="display-h text-2xl font-bold md:text-3xl">Остались вопросы?</h2>
                <p className="mt-3 max-w-xl text-mut">Личный руководитель проектов ответит в течение 15 минут в рабочее время. Если проще написать — пишите в Telegram, там же можно прислать фото площадки.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Btn onClick={() => openLead()}>Получить консультацию</Btn>
                <a href={TG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] transition-colors hover:border-accent hover:text-accent">
                  <Send size={15} /> Telegram
                </a>
              </div>
            </div>
          </div>
        </Reveal>

        <div className="mt-8 flex flex-wrap justify-center gap-3 pb-4">
          {[["Группа VK", "https://vk.com/clubsmproduction"], ["Rutube", "https://rutube.ru/channel/55924772/"], ["Pinterest", "https://ru.pinterest.com/SM_Production"], ["Яндекс Карты", MAP_ORG]].map(([t, url]) => (
            <a key={t} href={url} target="_blank" rel="noreferrer" className="rounded-full border border-line px-5 py-2.5 text-sm font-semibold text-mut transition-colors hover:border-accent hover:text-accent">{t}</a>
          ))}
        </div>
      </section>
    </>
  );
}
