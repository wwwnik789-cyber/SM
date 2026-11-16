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

