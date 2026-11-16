          {/* что увидите на визите */}
          <Reveal delay={0.06}>
            <div className="mt-5 rounded-3xl border border-line bg-card p-7 md:p-8">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <h3 className="display-h text-xl font-bold">Что увидите на визите</h3>
                <p className="text-sm text-mut">Без записи не проведём — производство действующее.</p>
              </div>
              <ul className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  "Станки в работе, а не на фото",
                  "Образцы плёнок, баннера, акрила и композита",
                  "Свою конструкцию до отправки на площадку",
                  "Как считается срок и что влияет на смету",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2.5 text-sm text-ink/85">
                    <Check size={16} className="mt-0.5 shrink-0 text-acid" /> {t}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

