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

