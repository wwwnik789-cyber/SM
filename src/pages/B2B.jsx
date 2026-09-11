import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn, SectionHead } from "../components/ui/bits";
import { Check, Clock, Factory, Spark } from "../components/ui/Icons";
import { useUI } from "../lib/store";

const benefits = [
  { icon: <Spark size={18} />, t: "Личный руководитель", d: "Человек, который ведёт смету, макеты, слот монтажа и правки в 23:00, если площадка сдвинула заезд." },
  { icon: <Clock size={18} />, t: "Срок в договоре", d: "Простые позиции — запуск от 3 часов, типовые фотозоны и press-wall часто закрываем за сутки." },
  { icon: <Factory size={18} />, t: "Документация для площадки", d: "Сертификаты на материалы, пожарка, паспорта конструкций, закрывающие документы." },
  { icon: <Check size={18} />, t: "Гибкая оплата", d: "Партнёрская сетка от объёма. Прозрачная смета — можно забрать в свою КП и накинуть маржу." },
];

const scopes = [
  { t: "Застройка площадки и оформление сцены", d: "Монтаж временных конструкций: сцены, подиумы, декорации, зоны регистрации, навигация. Каше садим миллиметр в миллиметр — знаем, где грузят через паркинг, а где лифт 1,2 м." },
  { t: "Имиджевые фотозоны, press-wall и brand-wall", d: "Самый частый вход в сотрудничество. Стандарт 2×2 … 5×3 м, печать BlackBack, в цене — каркас, печать, монтаж и демонтаж. Макет клиента проверяем, нет макета — собираем по брендбуку." },
  { t: "Уличные и выставочные стенды", d: "Сами считаем конструктив и парусность, а не просто печатаем баннер на чужой каркас. Ночной монтаж и согласование с площадкой фестиваля — на нас." },
];

const steps = [["Запрос", "Обратная связь от агентства с запросом на консультацию"], ["Консультация", "Обсуждение проекта и ТЗ с личным менеджером"], ["Согласование", "Фиксируем стоимость и сроки в договоре"], ["Выполнение", "Производство, доставка и установка конструкции"]];

export default function B2B() {
  usePageMeta("Сотрудничество с event-агентствами | SM-Production", "Партнёрская скидка и приоритетные сроки для event-агентств: производство и монтаж под ключ, прозрачные сметы, документация для площадок.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="Сотрудничество" title={<>Event-агентствам: партнёрская скидка <span className="text-accent">+ приоритетные сроки</span></>} text="Надёжное и творческое сотрудничество в полном цикле оформления и брендирования мероприятий. Мы не делим заказы на «достойные» и «мелкие».">
        <Btn onClick={() => openLead("Сотрудничество с агентством")} className="mt-8">Запрос на сотрудничество</Btn>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {benefits.map((b, i) => (
            <Reveal key={b.t} delay={i * 0.07}>
              <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                <span className="inline-flex rounded-2xl bg-accent/12 p-3 text-accent">{b.icon}</span>
                <h2 className="mt-4 font-display text-base font-bold">{b.t}</h2>
                <p className="mt-2.5 text-sm leading-relaxed text-mut">{b.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-24">
        <SectionHead overline="Контур работ" title="Какие задачи закрываем под ключ?" />
        <div className="grid gap-5 lg:grid-cols-3">
          {scopes.map((s, i) => (
            <Reveal key={s.t} delay={i * 0.08}>
              <div className="h-full rounded-3xl border border-line bg-bg2 p-7">
                <p className="display-h text-4xl font-black text-outline">0{i + 1}</p>
                <h3 className="mt-4 font-display text-lg font-bold">{s.t}</h3>
                <p className="mt-3 text-sm leading-relaxed text-mut">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-bg2 py-20">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Как начать" title="4 шага до первого совместного проекта" />
          <div className="grid gap-4 md:grid-cols-4">
            {steps.map(([t, d], i) => (
              <Reveal key={t} delay={i * 0.07}>
                <div className="relative h-full rounded-2xl border border-line bg-card p-6">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent font-display text-sm font-black text-white">{i + 1}</span>
                  <h3 className="mt-4 font-display text-base font-bold">{t}</h3>
                  <p className="mt-2 text-sm text-mut">{d}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Btn onClick={() => openLead("Сотрудничество с агентством")}>Получить консультацию</Btn>
          </div>
        </div>
      </section>
    </>
  );
}
