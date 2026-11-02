import { team } from "../data/team";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { useUI } from "../lib/store";

const palette = ["bg-accent", "bg-acid text-black", "bg-violet-500", "bg-sky-500", "bg-rose-500", "bg-emerald-500"];

export default function Team() {
  usePageMeta("Команда SM-Production — профессионалы оформления мероприятий", "Команда профессионалов с большим опытом на различных площадках, которая превращает идеи в реальность.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="Команда" title={<>Люди, которые превращают идеи <span className="text-accent">в реальность</span></>} text="Команда профессионалов с большим опытом на различных площадках. Вместе мы создаём яркие, качественные и запоминающиеся события!">
        <Btn to="/vakansii" variant="ghost" className="mt-8">Стать частью команды</Btn>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {team.map((m, i) => (
            <Reveal key={m.name} delay={(i % 4) * 0.06}>
              <div className="card-hover group h-full rounded-3xl border border-line bg-card p-6">
                <div className={`display-h flex h-20 w-20 items-center justify-center rounded-3xl text-2xl font-black text-white ${palette[i % palette.length]}`}>
                  {m.name.split(" ").map((w) => w[0]).join("")}
                </div>
                <h2 className="mt-5 font-display text-lg font-bold group-hover:text-accent">{m.name}</h2>
                <p className="mt-1 font-display text-[11px] uppercase tracking-[0.18em] text-accent">{m.role}</p>
                <p className="mt-3 text-sm leading-relaxed text-mut">{m.about}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1}>
          <div className="mt-14 grid gap-4 rounded-3xl border border-line bg-bg2 p-8 md:grid-cols-3 md:p-10">
            {[["24/7", "осуществляем монтажи без выходных"], ["3 часа", "печатаем баннер в срочном режиме"], ["2 города", "собственные цеха в Москве и СПб"]].map(([v, d]) => (
              <div key={v} className="text-center md:text-left">
                <p className="display-h text-4xl font-black text-accent">{v}</p>
                <p className="mt-2 text-sm text-mut">{d}</p>
              </div>
            ))}
          </div>
        </Reveal>

        <div className="mt-10 text-center">
          <button onClick={() => openLead("Хочу в команду")} className="link-underline font-display text-sm uppercase tracking-[0.2em] text-accent">
            Не нашли свою роль? Напишите нам
          </button>
        </div>
      </section>
    </>
  );
}
