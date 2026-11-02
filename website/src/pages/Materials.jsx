import { materials } from "../data/materials";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Check } from "../components/ui/Icons";

export default function Materials() {
  usePageMeta("Материалы и технологии — энциклопедия SM-Production", "Баннер BlackBack, ПВХ, акрил, алюминиевый профиль, зеркальный полистирол и другие материалы, с которыми мы работаем.");
  return (
    <>
      <PageHero overline="Энциклопедия" title={<>Материалы, с которыми <span className="text-accent">мы работаем</span></>} text="Коротко о том, из чего сделаны конструкции — и почему мы выбираем именно эти материалы. Поможем разобраться в конструктивах!" />

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {materials.map((m, i) => (
            <Reveal key={m.name} delay={(i % 3) * 0.06}>
              <div className="card-hover flex h-full flex-col rounded-3xl border border-line bg-card p-7">
                <div className="flex items-center justify-between">
                  <h2 className="display-h text-xl font-bold">{m.name}</h2>
                  <span className="rounded-full bg-accent/12 px-3 py-1 font-display text-[10px] uppercase tracking-widest text-accent">{m.use.split(",")[0]}</span>
                </div>
                <ul className="mt-5 space-y-2.5">
                  {m.props.map((p) => (
                    <li key={p} className="flex items-start gap-2.5 text-sm text-ink/85"><span className="mt-0.5 text-acid"><Check size={13} /></span>{p}</li>
                  ))}
                </ul>
                <p className="mt-5 border-t border-line pt-4 text-sm leading-relaxed text-mut">{m.note}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
