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

