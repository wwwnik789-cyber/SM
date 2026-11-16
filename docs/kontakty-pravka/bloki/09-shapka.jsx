      <PageHero
        overline="Контакты"
        title={<>Приезжайте в цех — <span className="text-accent">покажем, как делается ваш проект</span></>}
        text="Один адрес, один телефон и живые люди на связи круглосуточно. Производство в Москве на Остаповском проезде: здесь печатаем, фрезеруем, варим и собираем конструкции до отправки на площадку."
      >
        <div className="mt-8 flex flex-wrap gap-3">
          <a href={PHONE_HREF} className="btn-sheen inline-flex items-center gap-2 rounded-xl bg-accent px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] text-white">
            <Phone size={15} /> {PHONE}
          </a>
          <a href={`mailto:${EMAIL}`} className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent">
            <Mail size={15} /> {EMAIL}
          </a>
          <a href={TG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent">
            <Send size={15} /> Telegram
          </a>
        </div>
        <div className="mt-7 flex flex-wrap items-center gap-x-7 gap-y-3 text-sm text-mut">
          <span className="inline-flex items-center gap-2"><span className="animate-pulse-dot h-2 w-2 rounded-full bg-acid" /> На связи прямо сейчас</span>
          <span className="inline-flex items-center gap-2"><Clock size={14} className="text-accent" /> {HOURS}</span>
        </div>
      </PageHero>

