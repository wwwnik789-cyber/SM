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

