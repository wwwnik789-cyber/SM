      {/* ---------- адрес производства ---------- */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <Reveal>
          <div className="overflow-hidden rounded-[28px] border border-line bg-card">
            <div className="grid lg:grid-cols-[1.05fr_1fr]">
              <div className="relative p-8 md:p-11">
                <div className="grid-bg pointer-events-none absolute inset-0 opacity-30" aria-hidden="true" />
                <div className="relative">
                  <div className="mb-4 flex items-center gap-3">
                    <span className="h-2 w-2 rotate-45 bg-accent" />
                    <span className="font-display text-xs uppercase tracking-[0.28em] text-mut">Производство и офис · Москва</span>
                  </div>
                  <h2 className="display-h max-w-md text-3xl font-bold md:text-4xl">Наш адрес в Москве</h2>

                  <div className="mt-8 space-y-5">
                    <p className="flex items-start gap-3 text-ink/85">
                      <MapPin size={18} className="mt-0.5 shrink-0 text-accent" />
                      <span>{ADDRESS}</span>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Clock size={18} className="mt-0.5 shrink-0 text-accent" />
                      <span>{HOURS}</span>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Phone size={18} className="mt-0.5 shrink-0 text-accent" />
                      <a href={PHONE_HREF} className="link-underline font-display text-base font-bold text-ink">{PHONE}</a>
                    </p>
                    <p className="flex items-start gap-3 text-mut">
                      <Mail size={18} className="mt-0.5 shrink-0 text-accent" />
                      <a href={`mailto:${EMAIL}`} className="link-underline text-ink/85">{EMAIL}</a>
                    </p>
                  </div>

                  <div className="mt-9 flex flex-wrap gap-3">
                    <a href={MAP} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-5 py-3 text-sm font-semibold transition-colors hover:border-accent hover:text-accent">
                      Построить маршрут <ArrowUpRight size={14} />
                    </a>
                    <button onClick={() => openLead("Визит на производство")} className="inline-flex items-center gap-2 rounded-xl border border-line px-5 py-3 text-sm font-semibold transition-colors hover:border-accent hover:text-accent">
                      Записаться на визит
                    </button>
                  </div>
                  <p className="mt-5 text-xs text-mut">Визит — по предварительной записи: так вас встретят и проведут по цеху.</p>
                </div>
              </div>

              <div className="relative min-h-[320px] border-t border-line lg:border-l lg:border-t-0">
                <img src="/media/workshop.jpg" alt="Производственный цех SM-Production" loading="lazy" className="absolute inset-0 h-full w-full object-cover opacity-60" />
                <div className="absolute inset-0 bg-gradient-to-tr from-black/85 via-black/45 to-black/10" />
                <div className="relative flex h-full flex-col justify-between p-8 md:p-10">
                  <div className="flex justify-end">
                    <a href={MAP_ORG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-black/30 px-4 py-2 text-xs font-semibold text-white/90 backdrop-blur transition-colors hover:border-acid hover:text-acid">
                      Карточка в Яндекс Картах <ArrowUpRight size={13} />
                    </a>
                  </div>
                  <div>
                    <p className="font-display text-[10px] uppercase tracking-[0.3em] text-acid">Свой цех</p>
                    <p className="mt-3 max-w-xs text-sm leading-relaxed text-white/80">
                      ЧПУ-фрезер, УФ-принтер, сварка и зона сборки в одном контуре. Конструкцию собирают целиком до выезда на площадку.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

