      {/* ---------- финал ---------- */}
      <section className="mx-auto max-w-7xl px-5 pb-6">
        <Reveal>
          <div className="relative overflow-hidden rounded-[28px] border border-line bg-card p-9 md:p-12">
            <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/15 blur-[110px]" aria-hidden="true" />
            <div className="relative flex flex-col items-start justify-between gap-7 md:flex-row md:items-center">
              <div>
                <h2 className="display-h text-2xl font-bold md:text-3xl">Остались вопросы?</h2>
                <p className="mt-3 max-w-xl text-mut">Личный руководитель проектов ответит в течение 15 минут в рабочее время. Если проще написать — пишите в Telegram, там же можно прислать фото площадки.</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Btn onClick={() => openLead()}>Получить консультацию</Btn>
                <a href={TG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] transition-colors hover:border-accent hover:text-accent">
                  <Send size={15} /> Telegram
                </a>
              </div>
            </div>
          </div>
        </Reveal>

        <div className="mt-8 flex flex-wrap justify-center gap-3 pb-4">
          {[["Группа VK", "https://vk.com/clubsmproduction"], ["Rutube", "https://rutube.ru/channel/55924772/"], ["Pinterest", "https://ru.pinterest.com/SM_Production"], ["Яндекс Карты", MAP_ORG]].map(([t, url]) => (
            <a key={t} href={url} target="_blank" rel="noreferrer" className="rounded-full border border-line px-5 py-2.5 text-sm font-semibold text-mut transition-colors hover:border-accent hover:text-accent">{t}</a>
          ))}
        </div>
      </section>
    </>
  );
}
