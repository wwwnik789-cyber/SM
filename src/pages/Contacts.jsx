import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { ArrowUpRight, Clock, Mail, MapPin, Phone, Send } from "../components/ui/Icons";
import { EMAIL, PHONE, PHONE_HREF, TG } from "../lib/format";
import { useUI } from "../lib/store";

const offices = [
  { city: "Москва", addr: "109316, Остаповский проезд, д. 9, с. 13", phone: "+7 495 799-00-19", href: PHONE_HREF, hours: "Работаем 24/7 · производство 9:00–22:00", map: "https://yandex.ru/maps/?ll=37.714032%2C55.722381&z=15" },
  { city: "Санкт-Петербург", addr: "Швецова ул., д. 41, лит. А", phone: "+7 812 985-50-21", href: "tel:+78129855021", hours: "Работаем 24/7 · производство 10:00–19:00", map: "https://yandex.ru/maps/?ll=30.291082%2C59.897380&z=17" },
];

export default function Contacts() {
  usePageMeta("Контакты SM Production — Москва и Санкт-Петербург", "Телефоны, адреса производств и соцсети SM-Production. Работаем 24/7 без выходных.");
  const { openLead } = useUI();
  return (
    <>
      <PageHero overline="Контакты" title={<>Мы на связи <span className="text-accent">24/7</span></>} text="Позвоните, напишите в мессенджер или приезжайте на производство — покажем станки и ваши конструкции до отправки на площадку.">
        <div className="mt-8 flex flex-wrap gap-3">
          <a href={PHONE_HREF} className="btn-sheen inline-flex items-center gap-2 rounded-xl bg-accent px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] text-white"><Phone size={15} /> {PHONE}</a>
          <a href={`mailto:${EMAIL}`} className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent"><Mail size={15} /> {EMAIL}</a>
          <a href={TG} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-line px-7 py-4 font-display text-[13px] uppercase tracking-[0.14em] hover:border-accent hover:text-accent"><Send size={15} /> Telegram</a>
        </div>
      </PageHero>

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-5 lg:grid-cols-2">
          {offices.map((o, i) => (
            <Reveal key={o.city} delay={i * 0.08}>
              <div className="card-hover relative overflow-hidden rounded-3xl border border-line bg-card p-8">
                <div className="grid-bg absolute inset-0 opacity-40" />
                <div className="relative">
                  <h2 className="display-h text-3xl font-black">{o.city}</h2>
                  <p className="mt-4 flex items-start gap-2.5 text-mut"><MapPin size={16} className="mt-0.5 shrink-0 text-accent" /> {o.addr}</p>
                  <p className="mt-2 flex items-center gap-2.5 text-mut"><Clock size={16} className="shrink-0 text-accent" /> {o.hours}</p>
                  <a href={o.href} className="mt-4 inline-block font-display text-xl font-bold text-accent">{o.phone}</a>
                  <div className="mt-6 flex gap-3">
                    <a href={o.map} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 rounded-xl border border-line px-5 py-3 text-sm font-semibold hover:border-accent hover:text-accent">
                      Открыть в Яндекс Картах <ArrowUpRight size={14} />
                    </a>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1}>
          <div className="mt-8 flex flex-col items-center justify-between gap-6 rounded-3xl border border-line bg-bg2 p-10 text-center md:flex-row md:text-left">
            <div>
              <h2 className="display-h text-2xl font-bold">Остались вопросы?</h2>
              <p className="mt-2 text-mut">Личный руководитель проектов ответит в течение 15 минут в рабочее время.</p>
            </div>
            <Btn onClick={() => openLead()}>Получить консультацию</Btn>
          </div>
        </Reveal>

        <div className="mt-8 flex flex-wrap justify-center gap-3 pb-4">
          {[["Группа VK", "https://vk.com/clubsmproduction"], ["Rutube", "https://rutube.ru/channel/55924772/"], ["Pinterest", "https://ru.pinterest.com/SM_Production"], ["Яндекс Карты", "https://yandex.ru/maps/org/sm_production/135757112868"]].map(([t, url]) => (
            <a key={t} href={url} target="_blank" rel="noreferrer" className="rounded-full border border-line px-5 py-2.5 text-sm font-semibold text-mut transition-colors hover:border-accent hover:text-accent">{t}</a>
          ))}
        </div>
      </section>
    </>
  );
}
