import { Link } from "react-router-dom";
import { getService } from "../data/services";
import { SITE_URL, usePageMeta } from "../hooks/usePageMeta";
import { Accordion, Btn } from "../components/ui/bits";
import { Reveal } from "../components/ui/motion";
import { ArrowRight, Check, Clock, Factory, MapPin, Phone, Ruler, Spark } from "../components/ui/Icons";
import { useUI } from "../lib/store";

const service = getService("oformlenie-avtosalonov");

const quickFacts = [
  { icon: <Spark size={18} />, title: "Единая визуальная система", text: "Интерьер, POS, навигация, фасад и событие работают в одном стиле." },
  { icon: <Clock size={18} />, title: "Монтаж по графику салона", text: "Планируем работы до открытия, после закрытия или поэтапно по зонам." },
  { icon: <Factory size={18} />, title: "Производство в одном проекте", text: "Печать, конструкции, упаковка, доставка и монтаж без разрыва ответственности." },
  { icon: <MapPin size={18} />, title: "Один или несколько адресов", text: "Формируем спецификации и маркируем комплекты для каждого дилерского центра." },
];

const solutions = [
  {
    tag: "Быстрый старт",
    title: "Сезонное обновление",
    text: "Обновляем ключевые точки контакта под акцию, спецпредложение или маркетинговый календарь марки.",
    image: "/media/dealer-seasonal-pos.jpg",
    alt: "Концепция сезонного POS-оформления автомобильного шоурума",
    items: ["витринная и напольная графика", "Roll Up, баннеры и мобильные стенды", "информационные стойки и POS", "комплекты по адресам"],
  },
  {
    tag: "Клиентское событие",
    title: "Презентация модели",
    text: "Собираем пространство запуска внутри работающего шоурума с учётом автомобиля, гостей и технических ограничений.",
    image: "/media/dealer-model-launch.jpg",
    alt: "Концепция оформления презентации новой модели автомобиля",
    items: ["подиум и презентационный фон", "регистрация, фотозона и навигация", "декоративный свет и объёмная графика", "монтаж и демонтаж по графику"],
  },
  {
    tag: "Постоянное решение",
    title: "Обновление пространства",
    text: "Проектируем элементы постоянных зон под архитектуру салона, брендбук и ежедневную эксплуатацию.",
    image: "/media/dealer-reception-delivery.jpg",
    alt: "Концепция оформления ресепшн и зоны выдачи автомобиля",
    items: ["ресепшн и консультационные зоны", "зона торжественной выдачи", "световые логотипы и панели", "интерьерная навигация"],
  },
];

const zones = [
  { n: "01", title: "Фасад и вход", text: "Витринная графика, световые элементы, входная группа, пилоны и направление движения." },
  { n: "02", title: "Шоурум и консультация", text: "POS-носители, стойки, брендированные стены и сменные материалы кампаний." },
  { n: "03", title: "Зона выдачи", text: "Фоновые панели, декоративный свет, подиум и аккуратный сценарий фотографии." },
  { n: "04", title: "Сервис и автомобили с пробегом", text: "Понятная навигация, зонирование, информационные стенды и мобильные решения." },
];

const rollout = [
  "единый стандарт и перечень носителей для всей сети",
  "паспорт размеров и условий монтажа по каждому адресу",
  "маркировка упаковки по центрам, помещениям и очередям работ",
  "согласованный календарь производства, доставки и монтажа",
  "фотофиксация комплектности и результата после установки",
];

const process = [
  ["Экспресс-аудит", "Получаем фотографии или план, уточняем задачу, адрес и желаемую дату."],
  ["Замер и бриф", "Проверяем размеры, основания, электрику, маршруты клиентов и ограничения объекта."],
  ["Концепция", "Адаптируем брендбук и показываем состав носителей до запуска производства."],
  ["Смета и график", "Фиксируем материалы, объём, логистику и последовательность монтажных работ."],
  ["Производство", "Печатаем графику, изготавливаем конструкции, собираем и маркируем комплекты."],
  ["Монтаж и сдача", "Устанавливаем в согласованное время, проверяем результат и передаём объект."],
];

const consultationInputs = [
  "фотографии или короткое видео зоны",
  "примерные размеры или план",
  "брендбук и макеты, если есть",
  "адрес и количество дилерских центров",
  "желаемая дата готовности",
];

export default function Dealerships() {
  const { openLead } = useUI();
  const path = "/uslugi/oformlenie-avtosalonov";
  const requestConsultation = () => openLead("Оформление автосалона");
  const schema = [
    {
      "@type": "Service",
      "@id": `${SITE_URL}${path}#service`,
      name: service.title,
      description: service.seoDescription,
      url: `${SITE_URL}${path}`,
      image: `${SITE_URL}${service.image}`,
      provider: { "@id": `${SITE_URL}/#organization` },
      areaServed: ["Москва", "Московская область", "Россия"],
      serviceType: ["Оформление автосалонов", "Брендинг дилерских центров", "POS-материалы", "Монтаж рекламных конструкций"],
    },
    {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Главная", item: `${SITE_URL}/` },
        { "@type": "ListItem", position: 2, name: "Услуги", item: `${SITE_URL}/uslugi` },
        { "@type": "ListItem", position: 3, name: service.title, item: `${SITE_URL}${path}` },
      ],
    },
    {
      "@type": "FAQPage",
      mainEntity: service.faq.map((item) => ({
        "@type": "Question",
        name: item.q,
        acceptedAnswer: { "@type": "Answer", text: item.a },
      })),
    },
  ];

  usePageMeta({
    title: service.seoTitle,
    description: service.seoDescription,
    path,
    image: service.image,
    schema,
  });

  return (
    <div className="bg-[#0b0d10] text-white">
      <section className="relative flex min-h-[840px] items-end overflow-hidden pt-32 md:min-h-[900px]">
        <img
          src="/media/dealer-branding-hero.jpg"
          alt="Концепция комплексного оформления современного дилерского центра"
          className="absolute inset-0 h-full w-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(5,7,9,.96)_0%,rgba(5,7,9,.72)_48%,rgba(5,7,9,.22)_100%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(0deg,#0b0d10_0%,transparent_45%,rgba(5,7,9,.45)_100%)]" />
        <div className="grid-bg absolute inset-0 opacity-[0.08]" />

        <div className="relative mx-auto w-full max-w-7xl px-5 pb-14 md:pb-20">
          <nav className="mb-10 text-xs text-white/55" aria-label="Хлебные крошки">
            <Link to="/" className="transition-colors hover:text-white">Главная</Link>
            <span className="mx-2">/</span>
            <Link to="/uslugi" className="transition-colors hover:text-white">Услуги</Link>
            <span className="mx-2">/</span>
            <span className="text-white">Оформление автосалонов</span>
          </nav>

          <Reveal>
            <div className="max-w-4xl">
              <div className="mb-6 flex items-center gap-3">
                <span className="h-px w-12 bg-accent" />
                <span className="font-display text-[11px] uppercase tracking-[0.28em] text-white/70">Решения для дилерских центров</span>
              </div>
              <h1 className="display-h text-4xl font-black leading-[0.98] sm:text-5xl md:text-7xl lg:text-[5.25rem]">
                Оформление автосалонов <span className="text-accent">и дилерских центров</span>
              </h1>
              <p className="mt-7 max-w-2xl text-base leading-relaxed text-white/72 md:text-xl">
                Проектируем, производим и монтируем интерьер, POS, зоны выдачи, презентации моделей, навигацию и фасадные элементы — с учётом режима работающего салона.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Btn onClick={requestConsultation}>Заказать консультацию <Phone size={16} /></Btn>
                <a href="#solutions" className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/25 px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] text-white transition hover:border-white hover:bg-white/8">
                  Смотреть решения <ArrowRight size={16} />
                </a>
              </div>
            </div>
          </Reveal>

          <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/12 bg-white/12 sm:grid-cols-2 lg:grid-cols-4">
            {["Дизайн по брендбуку", "Собственное производство", "Доставка и монтаж", "Работа с сетью адресов"].map((item) => (
              <div key={item} className="bg-[#0b0d10]/85 px-5 py-4 text-sm font-semibold text-white/78 backdrop-blur-md">
                <span className="mr-2 text-accent">◆</span>{item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="sticky top-[72px] z-30 border-y border-white/10 bg-[#0b0d10]/92 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-7 overflow-x-auto px-5 py-4 text-xs font-semibold uppercase tracking-[0.14em] text-white/58">
          <a href="#solutions" className="shrink-0 transition hover:text-white">Форматы старта</a>
          <a href="#zones" className="shrink-0 transition hover:text-white">Зоны салона</a>
          <a href="#network" className="shrink-0 transition hover:text-white">Для дилерских групп</a>
          <a href="#process" className="shrink-0 transition hover:text-white">Процесс</a>
          <a href="#faq" className="shrink-0 transition hover:text-white">FAQ</a>
          <button onClick={requestConsultation} className="ml-auto shrink-0 text-accent transition hover:text-white">Консультация →</button>
        </div>
      </div>

      <section className="bg-[#ece9e1] py-20 text-[#17191d] md:py-28">
        <div className="mx-auto max-w-7xl px-5">
          <Reveal>
            <div className="grid gap-8 lg:grid-cols-[1.15fr_.85fr] lg:items-end">
              <div>
                <p className="font-display text-xs uppercase tracking-[0.28em] text-[#b74220]">От задачи — к единой системе</p>
                <h2 className="display-h mt-4 text-3xl font-black md:text-5xl">Оформление поддерживает весь клиентский маршрут</h2>
              </div>
              <p className="max-w-xl text-base leading-relaxed text-[#555960] md:text-lg">
                Витрина, ресепшн, зона консультации, автомобиль и точка выдачи не должны выглядеть как отдельные проекты. Связываем носители общей логикой и заранее учитываем монтаж, обслуживание и будущую смену кампаний.
              </p>
            </div>
          </Reveal>

          <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {quickFacts.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.06}>
                <article className="h-full border-t border-[#17191d]/20 bg-white/55 p-6">
                  <span className="inline-flex rounded-full bg-[#17191d] p-3 text-white">{item.icon}</span>
                  <h3 className="mt-5 font-display text-base font-bold">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#62656b]">{item.text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="solutions" className="scroll-mt-28 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-5">
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Три формата старта</p>
            <div className="mt-4 grid gap-7 lg:grid-cols-[1fr_.7fr] lg:items-end">
              <h2 className="display-h text-3xl font-black md:text-5xl">Начать можно с конкретной зоны или кампании</h2>
              <p className="leading-relaxed text-white/55">Не обязательно сразу обновлять весь дилерский центр. Выбираем понятный первый проект и закладываем возможность развития системы.</p>
            </div>
          </Reveal>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {solutions.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.08}>
                <article className="group h-full overflow-hidden rounded-[1.75rem] border border-white/12 bg-[#12151a]">
                  <div className="relative overflow-hidden">
                    <img src={item.image} alt={item.alt} loading="lazy" className="h-64 w-full object-cover transition duration-700 group-hover:scale-[1.04]" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#12151a] via-transparent to-transparent" />
                    <span className="absolute left-5 top-5 rounded-full border border-white/20 bg-black/45 px-3 py-1.5 font-display text-[10px] uppercase tracking-[0.18em] backdrop-blur">{item.tag}</span>
                  </div>
                  <div className="p-6 md:p-7">
                    <p className="font-display text-xs text-accent">0{index + 1}</p>
                    <h3 className="mt-3 font-display text-xl font-bold">{item.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-white/55">{item.text}</p>
                    <ul className="mt-6 space-y-3">
                      {item.items.map((line) => (
                        <li key={line} className="flex items-start gap-3 text-sm text-white/80">
                          <Check size={15} className="mt-0.5 shrink-0 text-accent" />{line}
                        </li>
                      ))}
                    </ul>
                  </div>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="zones" className="scroll-mt-28 border-y border-white/10 bg-[#101318] py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-5">
          <div className="grid gap-10 lg:grid-cols-[1.15fr_.85fr] lg:items-stretch">
            <Reveal>
              <figure className="relative h-full min-h-[520px] overflow-hidden rounded-[2rem] border border-white/10">
                <img src="/media/dealer-facade-navigation.jpg" alt="Концепция фасада и наружной навигации дилерского центра" loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
                <figcaption className="absolute inset-x-0 bottom-0 p-7 md:p-9">
                  <p className="font-display text-xs uppercase tracking-[0.24em] text-accent">От парковки до выдачи</p>
                  <h2 className="display-h mt-3 max-w-xl text-3xl font-black md:text-5xl">Один язык во всех зонах</h2>
                </figcaption>
              </figure>
            </Reveal>

            <div className="grid gap-4 sm:grid-cols-2">
              {zones.map((zone, index) => (
                <Reveal key={zone.title} delay={(index % 2) * 0.08}>
                  <article className="h-full rounded-3xl border border-white/10 bg-[#171b21] p-6">
                    <span className="font-display text-xs text-accent">{zone.n}</span>
                    <h3 className="mt-5 font-display text-lg font-bold">{zone.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-white/52">{zone.text}</p>
                  </article>
                </Reveal>
              ))}
              <Reveal className="sm:col-span-2">
                <div className="rounded-3xl border border-accent/35 bg-accent/10 p-6">
                  <p className="font-display text-sm font-bold">Начать можно с фотографии зоны</p>
                  <p className="mt-2 text-sm leading-relaxed text-white/58">Покажем, какие вводные потребуются дальше, и предложим следующий шаг без выдуманного ТЗ.</p>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      <section id="network" className="scroll-mt-28 bg-[#ece9e1] py-20 text-[#17191d] md:py-28">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-2 lg:items-center">
          <Reveal>
            <div>
              <p className="font-display text-xs uppercase tracking-[0.28em] text-[#b74220]">Для дилерских групп</p>
              <h2 className="display-h mt-4 text-3xl font-black md:text-5xl">Один стандарт — разные адреса</h2>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-[#555960] md:text-lg">
                При тиражировании важен не только макет. У каждого центра свои размеры, доступ, логистика и допустимое время работ. Поэтому единая концепция превращается в адресные спецификации и монтажный календарь.
              </p>
              <ul className="mt-8 space-y-4">
                {rollout.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm font-semibold text-[#303238]">
                    <span className="mt-0.5 rounded-full bg-[#17191d] p-1 text-white"><Check size={12} /></span>{item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="grid grid-cols-[.72fr_1fr] gap-3">
              <img src="/media/dealer-reception-delivery.jpg" alt="Оформление зоны выдачи автомобиля" loading="lazy" className="mt-14 h-[420px] w-full rounded-[1.75rem] object-cover" />
              <img src="/media/dealer-night-installation.jpg" alt="Монтаж оформления автосалона вне клиентского потока" loading="lazy" className="h-[500px] w-full rounded-[1.75rem] object-cover" />
            </div>
          </Reveal>
        </div>
      </section>

      <section id="process" className="scroll-mt-28 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-5">
          <Reveal>
            <div className="grid gap-6 lg:grid-cols-2 lg:items-end">
              <div>
                <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Процесс</p>
                <h2 className="display-h mt-4 text-3xl font-black md:text-5xl">От первой фотографии до готового объекта</h2>
              </div>
              <p className="max-w-xl leading-relaxed text-white/55">До производства фиксируем размеры, материалы, ответственных, условия доступа и график. Это снижает риск переделок на объекте.</p>
            </div>
          </Reveal>
          <ol className="mt-12 grid gap-px overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/10 md:grid-cols-2 lg:grid-cols-3">
            {process.map(([title, text], index) => (
              <li key={title} className="bg-[#12151a] p-7 md:min-h-56">
                <div className="flex items-center justify-between">
                  <span className="font-display text-xs text-accent">{String(index + 1).padStart(2, "0")}</span>
                  {index === 1 && <Ruler size={18} className="text-white/25" />}
                  {index === 4 && <Factory size={18} className="text-white/25" />}
                </div>
                <h3 className="mt-8 font-display text-lg font-bold">{title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-white/52">{text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="border-y border-white/10 bg-[#141820] py-20 md:py-28">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 lg:grid-cols-[1fr_.8fr] lg:items-center">
          <Reveal>
            <div>
              <p className="font-display text-xs uppercase tracking-[0.28em] text-accent">Первичная консультация</p>
              <h2 className="display-h mt-4 text-3xl font-black md:text-5xl">Не нужен идеальный бриф, чтобы начать разговор</h2>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-white/58">Покажите задачу и обозначьте дату. Менеджер уточнит недостающие вводные и согласует следующий шаг: консультацию, замер или предварительный состав работ.</p>
              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                {consultationInputs.map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/75">
                    <Check size={14} className="mt-0.5 shrink-0 text-accent" />{item}
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <aside className="rounded-[2rem] bg-accent p-7 text-white md:p-9">
              <p className="font-display text-xs uppercase tracking-[0.25em] text-white/70">Обсудить задачу</p>
              <h3 className="display-h mt-4 text-2xl font-black md:text-3xl">Закажите консультацию менеджера</h3>
              <p className="mt-4 text-sm leading-relaxed text-white/80">Оставьте имя и телефон. В заявке уже будет отмечено направление «Оформление автосалона».</p>
              <Btn onClick={requestConsultation} variant="acid" className="mt-7 w-full">Заказать консультацию <Phone size={16} /></Btn>
              <div className="mt-6 border-t border-white/20 pt-5 text-sm text-white/78">
                <a href="tel:+74957990019" className="font-display text-lg font-bold text-white transition hover:text-acid">+7 (495) 799-00-19</a>
                <p className="mt-2">Москва, Остаповский проезд, д. 9 с. 3</p>
              </div>
            </aside>
          </Reveal>
        </div>
      </section>

      <section id="faq" className="scroll-mt-28 bg-[#ece9e1] py-20 text-[#17191d] md:py-28">
        <div className="mx-auto max-w-4xl px-5">
          <Reveal>
            <p className="font-display text-xs uppercase tracking-[0.28em] text-[#b74220]">FAQ</p>
            <h2 className="display-h mb-10 mt-4 text-3xl font-black md:text-5xl">Частые вопросы дилерских центров</h2>
          </Reveal>
          <div className="[&_.text-mut]:text-[#555960] [&_.border-line]:border-[#17191d]/15 [&_button]:text-[#17191d] [&_button:hover]:text-[#b74220]">
            <Accordion items={service.faq} />
          </div>
          <div className="mt-12 flex flex-col items-start justify-between gap-5 border-t border-[#17191d]/15 pt-8 sm:flex-row sm:items-center">
            <p className="max-w-xl text-sm leading-relaxed text-[#62656b]">Интерьерные изображения являются концепт-визуализациями и показывают возможные направления оформления, а не реализованные кейсы.</p>
            <button onClick={requestConsultation} className="shrink-0 font-display text-xs uppercase tracking-[0.16em] text-[#b74220]">Заказать консультацию →</button>
          </div>
        </div>
      </section>
    </div>
  );
}
