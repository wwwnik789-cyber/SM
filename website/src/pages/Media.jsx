import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal, Marquee } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { Video } from "../components/ui/Icons";
import { useUI } from "../lib/store";

const blocks = [
  { t: "Студийная съёмка", d: "Профессиональная съёмка в оборудованной студии с контролируемым светом и звуком.", items: ["Съёмки в студии и на циклораме (хромакей, белая, чёрная)", "Запись видео-подкастов", "Съёмка шоу и прямых эфиров", "Создание индивидуальных декораций"] },
  { t: "Выездная съёмка", d: "Работаем на ваших площадках — от концертов до выставок.", items: ["Отчётные ролики для мероприятий", "Съёмка выставок и фестивалей", "Съёмка концертов и конференций", "Имиджевые и рекламные ролики"] },
  { t: "Монтаж и видео-контент", d: "Полный цикл постпродакшна и контент для экранов.", items: ["Рекламные и брендовые ролики", "2D/3D графика и анимация", "Event-видео (мероприятия, концерты)", "Контент для экранов и оформления"] },
];

export default function Media() {
  usePageMeta("SM-Media — видеопроизводство под ключ | SM-Production", "Создание видеороликов под ключ: студийная и выездная съёмка, монтаж, анимация и звук для ваших событий и бизнеса.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="SM-Media" title={<>Создание видеороликов <span className="text-accent">под ключ</span></>} text="Делаем яркие, эффективные, брендовые видео для ваших событий и бизнеса. Профессиональная команда, современные технологии, индивидуальный подход.">
        <Btn onClick={() => openLead("SM-Media")} className="mt-8">Получить консультацию</Btn>
      </PageHero>

      <Marquee items={["Студия", "Съёмки", "Сценарии", "Монтаж", "Звук", "Анимации"]} className="border-y border-line py-5" />

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="grid gap-5 lg:grid-cols-3">
          {blocks.map((b, i) => (
            <Reveal key={b.t} delay={i * 0.08}>
              <div className="card-hover flex h-full flex-col rounded-3xl border border-line bg-card p-7">
                <span className="inline-flex w-fit rounded-2xl bg-accent/12 p-3.5 text-accent"><Video size={20} /></span>
                <h2 className="display-h mt-5 text-xl font-bold">{b.t}</h2>
                <p className="mt-2 text-sm text-mut">{b.d}</p>
                <ul className="mt-5 space-y-2.5 border-t border-line pt-5 text-sm text-ink/80">
                  {b.items.map((it) => <li key={it} className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rotate-45 bg-acid" />{it}</li>)}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1}>
          <div className="img-zoom relative mt-6 overflow-hidden rounded-3xl border border-line">
            <img src="/media/studio.jpg" alt="Студия SM-Media" className="h-[380px] w-full object-cover md:h-[480px]" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
            <div className="absolute bottom-0 p-8">
              <p className="font-display text-xs uppercase tracking-[0.3em] text-acid">Декорации + съёмка в одной смете</p>
              <h3 className="display-h mt-2 max-w-lg text-2xl font-bold text-white">Экономим день площадки: производство и медиа работают вместе</h3>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
