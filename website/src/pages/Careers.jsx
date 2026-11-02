import { vacancies } from "../data/vacancies";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn, ArrowLink } from "../components/ui/bits";
import { Bolt, Factory, Spark } from "../components/ui/Icons";
import { useUI } from "../lib/store";

export default function Careers() {
  usePageMeta("Вакансии SM-Production — работа в рекламном производстве", "Монтажники, дизайнеры и менеджеры проектов: присоединяйтесь к команде, которая превращает идеи в реальность.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="Карьера" title={<>Делайте события <span className="text-accent">вместе с нами</span></>} text="Мы — команда, для которой работа это искусство делать людей счастливыми в особенный для них день. Присоединяйтесь!">
        <Btn onClick={() => openLead("Хочу в команду")} className="mt-8">Откликнуться</Btn>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="mb-12 grid gap-4 md:grid-cols-3">
          {[
            [<Factory size={18} key="1" />, "Настоящий цех", "750 м², УФ-печать, фрезеровка — есть на чём расти"],
            [<Bolt size={18} key="2" />, "Живые проекты", "От фотозон до фестивалей: VK Fest, РЖД Арена, Сколково"],
            [<Spark size={18} key="3" />, "Рост", "Обучение и прозрачный путь до бригадира и руководителя"],
          ].map(([icon, t, d], i) => (
            <Reveal key={t} delay={i * 0.07}>
              <div className="flex items-center gap-4 rounded-2xl border border-line bg-card p-5">
                <span className="rounded-2xl bg-acid/15 p-3 text-acid">{icon}</span>
                <div><p className="font-display text-sm font-bold">{t}</p><p className="text-xs text-mut">{d}</p></div>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="space-y-4">
          {vacancies.map((v, i) => (
            <Reveal key={v.title} delay={i * 0.06}>
              <div className="card-hover flex flex-col justify-between gap-5 rounded-3xl border border-line bg-card p-7 md:flex-row md:items-center">
                <div>
                  <h2 className="display-h text-xl font-bold">{v.title}</h2>
                  <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mut">{v.text}</p>
                </div>
                <div className="flex shrink-0 items-center gap-5">
                  <span className="font-display text-lg font-black text-accent">{v.money}</span>
                  <button onClick={() => openLead(`Вакансия: ${v.title}`)} className="rounded-xl border border-line px-5 py-3 font-display text-xs uppercase tracking-widest hover:border-accent hover:text-accent">
                    Откликнуться
                  </button>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-12"><ArrowLink to="/team">Познакомиться с командой</ArrowLink></div>
      </section>
    </>
  );
}
