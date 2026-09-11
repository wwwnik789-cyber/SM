import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "motion/react";
import { useRef } from "react";
import { usePageMeta } from "../hooks/usePageMeta";
import { useUI } from "../lib/store";
import { services } from "../data/services";
import { portfolio } from "../data/portfolio";
import { posts } from "../data/blog";
import { companyStats, values } from "../data/team";
import { production } from "../data/production";
import { Counter, Marquee, Reveal } from "../components/ui/motion";
import { ArrowLink, Btn, SectionHead } from "../components/ui/bits";
import { ArrowRight, ArrowUpRight, Bolt, Clock, Cube, Factory, Spark, Video } from "../components/ui/Icons";

function KineticTitle({ line1, line2 }) {
  const words = [...line1.split(" "), ...line2.split(" ")];
  return (
    <h1 className="display-h text-[clamp(2.4rem,7vw,5.6rem)] font-black leading-[1.02]">
      {line1.split(" ").map((w, i) => (
        <motion.span key={"a" + i} initial={{ y: "110%", opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.35 + i * 0.07, duration: 0.7, ease: [0.2, 0.65, 0.25, 1] }} className="mr-[0.28em] inline-block overflow-hidden align-top">
          <span className="inline-block">{w}</span>
        </motion.span>
      ))}
      <br />
      {line2.split(" ").map((w, i) => (
        <motion.span key={"b" + i} initial={{ y: "110%", opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 + i * 0.07, duration: 0.7, ease: [0.2, 0.65, 0.25, 1] }} className="mr-[0.28em] inline-block overflow-hidden align-top">
          <span className="inline-block text-outline-accent">{w}</span>
        </motion.span>
      ))}
      <span className="sr-only">{line1} {line2}</span>
    </h1>
  );
}

export default function Home() {
  usePageMeta("SM-Production — оформление мероприятий и декорации под ключ в Москве и СПб", "Производство полного цикла: фотозоны, стенды, световые вывески, оформление сцен и застройка мероприятий. Москва и СПб, монтаж 24/7.");
  const { openLead } = useUI();
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [0, 140]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.12]);

  return (
    <>
      {/* HERO */}
      <section ref={heroRef} className="relative flex min-h-svh items-center overflow-hidden pt-28">
        <motion.div style={{ y, scale }} className="absolute inset-0">
          <img src="/media/hero-stage.jpg" alt="Сцена, оформленная SM-Production" className="h-full w-full object-cover" />
        </motion.div>
        <div className="absolute inset-0 bg-gradient-to-t from-bg via-bg/72 to-bg/30" />
        <div className="grid-bg absolute inset-0 opacity-30" />

        <div className="relative z-10 mx-auto w-full max-w-7xl px-5 pb-16">
          <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mb-6 inline-flex items-center gap-3 rounded-full border border-line glass px-4 py-2 font-display text-[11px] uppercase tracking-[0.3em] text-ink">
            <span className="h-2 w-2 animate-pulse-dot rounded-full bg-acid" /> event · branding · decor · 24/7
          </motion.p>

          <KineticTitle line1="Оформление" line2="мероприятий под ключ" />

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9, duration: 0.7 }} className="mt-7 max-w-xl text-base leading-relaxed text-mut md:text-lg">
            SM Production — производство полного цикла: от концепции и 3D-визуализации до монтажа фотозон, стендов и сцен в Москве и Санкт-Петербурге.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.05 }} className="mt-9 flex flex-wrap items-center gap-4">
            <Btn onClick={() => openLead()}>Получить консультацию <ArrowRight size={15} /></Btn>
            <Btn to="/portfolio" variant="ghost">Смотреть портфолио</Btn>
          </motion.div>

          {/* bento quick cards */}
          <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { t: "Срочный заказ", d: "фотозоны, пресс-воллы, баннеры — за 24 часа", to: "/uslugi/akciya-fotozona", icon: <Bolt size={18} /> },
              { t: "Конференция под ключ", d: "сцена + каше + фотозона, от 89 000 ₽", to: "/uslugi/oformlenie-stseny", icon: <Factory size={18} /> },
              { t: "Аренда оборудования", d: "свет, звук, мебель, фотобудки", to: "/arenda", icon: <Cube size={18} /> },
              { t: "Калькулятор", d: "смета фотозоны за 1 минуту", to: "/kalkulyator", icon: <Spark size={18} /> },
            ].map((c, i) => (
              <motion.div key={c.t} initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.15 + i * 0.1 }}>
                <Link to={c.to} className="card-hover group flex h-full flex-col justify-between gap-6 rounded-2xl border border-line glass p-5">
                  <div className="flex items-center justify-between text-accent">
                    {c.icon}
                    <ArrowUpRight size={16} className="text-mut transition-all group-hover:translate-x-1 group-hover:-translate-y-1 group-hover:text-accent" />
                  </div>
                  <div>
                    <p className="font-display text-sm font-bold">{c.t}</p>
                    <p className="mt-1.5 text-xs leading-relaxed text-mut">{c.d}</p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <Marquee items={["Фотозоны", "Выставочные стенды", "Световые вывески", "Оформление сцен", "Баннеры", "Бренд-зоны", "Интерактив", "Аренда", "SM-Media"]} className="border-y border-line py-5" />

      {/* STATS */}
      <section className="mx-auto max-w-7xl px-5 py-20 md:py-28">
        <div className="grid gap-10 md:grid-cols-4">
          {companyStats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.08}>
              <div className="border-l-2 border-accent pl-6">
                <p className="display-h text-5xl font-black md:text-6xl">
                  <Counter value={s.value} suffix={s.suffix} />
                </p>
                <p className="mt-3 text-sm text-mut">{s.label}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* SERVICES BENTO */}
      <section className="mx-auto max-w-7xl px-5 pb-24">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <SectionHead overline="Услуги" title={<>Что мы производим <span className="text-accent">и монтируем</span></>} className="mb-0" />
          <ArrowLink to="/uslugi" className="mb-2">Все услуги</ArrowLink>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {services.slice(0, 9).map((s, i) => (
            <Reveal key={s.slug} delay={(i % 3) * 0.07} className={i === 0 ? "md:col-span-2 md:row-span-2" : ""}>
              <Link to={`/uslugi/${s.slug}`} className="card-hover img-zoom group relative flex h-full min-h-[210px] flex-col justify-end overflow-hidden rounded-3xl border border-line">
                <img src={s.image} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover opacity-60 transition-opacity group-hover:opacity-80" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />
                <div className="relative p-6">
                  <p className="font-display text-[10px] uppercase tracking-[0.26em] text-acid">{s.category}</p>
                  <h3 className="display-h mt-2 text-xl font-bold text-white">{s.title}</h3>
                  {i === 0 && <p className="mt-3 max-w-md text-sm leading-relaxed text-white/70">{s.short}</p>}
                </div>
                <span className="absolute right-5 top-5 rounded-full border border-white/25 p-2.5 text-white opacity-0 transition-all duration-300 group-hover:opacity-100"><ArrowUpRight size={16} /></span>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      {/* PORTFOLIO horizontal */}
      <section className="border-y border-line bg-bg2 py-24">
        <div className="mx-auto max-w-7xl px-5">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <SectionHead overline="Портфолио" title="Недавние проекты команды" className="mb-0" />
            <ArrowLink to="/portfolio" className="mb-2">Все кейсы</ArrowLink>
          </div>
        </div>
        <div className="mt-12 flex gap-5 overflow-x-auto px-5 pb-6 [scrollbar-width:none] md:px-[max(1.25rem,calc((100vw-80rem)/2+1.25rem))]">
          {portfolio.slice(0, 7).map((p) => (
            <Link key={p.slug} to={`/portfolio/${p.slug}`} className="card-hover img-zoom group relative w-[320px] shrink-0 overflow-hidden rounded-3xl border border-line md:w-[400px]">
              <img src={p.image} alt={p.title} loading="lazy" className="h-[420px] w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />
              <div className="absolute inset-x-0 bottom-0 p-6">
                <p className="font-display text-[10px] uppercase tracking-[0.24em] text-acid">{p.year} · {p.client}</p>
                <h3 className="display-h mt-2 text-xl font-bold text-white">{p.title}</h3>
                <p className="mt-1 text-xs text-white/60">{p.place}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* PROCESS mini-timeline */}
      <section className="mx-auto max-w-7xl px-5 py-24">
        <SectionHead overline="Процессы" title="Как рождается ваш проект" text="Четыре прозрачных этапа — от заявки до демонтажа и обратной связи." />
        <div className="grid gap-4 md:grid-cols-4">
          {[
            ["01", "Обсуждаем задачу", "Глубокая консультация, прозрачное КП и ТЗ, согласованные до мелочей."],
            ["02", "Концепция и производство", "Дизайн, 3D-визуализации и собственный цех 750 м²."],
            ["03", "Монтаж и поддержка", "Логистика, профессиональный монтаж и техподдержка на событии."],
            ["04", "Демонтаж и отзывы", "Аккуратно вывозим конструкции и собираем обратную связь."],
          ].map(([n, t, d], i) => (
            <Reveal key={n} delay={i * 0.08}>
              <div className="group relative h-full rounded-3xl border border-line bg-card p-7 transition-colors hover:border-accent">
                <span className="text-outline display-h text-5xl font-black transition-all group-hover:text-accent group-hover:[-webkit-text-stroke:0px]">{n}</span>
                <h3 className="mt-6 font-display text-lg font-bold">{t}</h3>
                <p className="mt-3 text-sm leading-relaxed text-mut">{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <div className="mt-10"><ArrowLink to="/process">Изучить процессы подробнее</ArrowLink></div>
      </section>

      {/* PRODUCTION + MEDIA split */}
      <section className="mx-auto grid max-w-7xl gap-4 px-5 pb-24 lg:grid-cols-2">
        <Reveal>
          <Link to="/proizvodstvo" className="card-hover img-zoom group relative flex min-h-[420px] flex-col justify-end overflow-hidden rounded-3xl border border-line">
            <img src="/media/lightbox.jpg" alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 to-black/10" />
            <div className="relative p-8">
              <p className="font-display text-[10px] uppercase tracking-[0.26em] text-acid">Производство под заказ</p>
              <h3 className="display-h mt-3 text-3xl font-bold text-white">Световые вывески, короба, объёмные буквы</h3>
              <p className="mt-3 max-w-md text-sm text-white/70">{production.length} направлений собственного цеха — от дизайна до установки.</p>
            </div>
          </Link>
        </Reveal>
        <Reveal delay={0.1}>
          <Link to="/media" className="card-hover img-zoom group relative flex min-h-[420px] flex-col justify-end overflow-hidden rounded-3xl border border-line">
            <img src="/media/studio.jpg" alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 to-black/10" />
            <div className="relative p-8">
              <p className="flex items-center gap-2 font-display text-[10px] uppercase tracking-[0.26em] text-acid"><Video size={14} /> SM-Media</p>
              <h3 className="display-h mt-3 text-3xl font-bold text-white">Видеопроизводство для ваших событий</h3>
              <p className="mt-3 max-w-md text-sm text-white/70">Студийная и выездная съёмка, монтаж и брендовые ролики под ключ.</p>
            </div>
          </Link>
        </Reveal>
      </section>

      {/* WHY */}
      <section className="border-y border-line bg-bg2 py-24">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHead overline="Почему мы" title="Почему выбирают SM-Production?" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {values.map((v, i) => (
              <Reveal key={v.title} delay={i * 0.07}>
                <div className="card-hover h-full rounded-3xl border border-line bg-card p-7">
                  <span className="inline-flex rounded-2xl bg-accent/12 p-3 text-accent"><Clock size={20} /></span>
                  <h3 className="mt-5 font-display text-lg font-bold">{v.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-mut">{v.text}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* BLOG teaser */}
      <section className="mx-auto max-w-7xl px-5 py-24">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <SectionHead overline="Блог" title="Новости и кейсы" className="mb-0" />
          <ArrowLink to="/blog" className="mb-2">Читать блог</ArrowLink>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {posts.slice(0, 3).map((p, i) => (
            <Reveal key={p.slug} delay={i * 0.08}>
              <Link to={`/blog/${p.slug}`} className="card-hover img-zoom group block h-full overflow-hidden rounded-3xl border border-line bg-card">
                <div className="overflow-hidden"><img src={p.cover} alt="" loading="lazy" className="h-52 w-full object-cover" /></div>
                <div className="p-6">
                  <p className="font-display text-[10px] uppercase tracking-[0.24em] text-accent">{p.tag} · {p.read} мин</p>
                  <h3 className="display-h mt-3 text-lg font-bold leading-snug group-hover:text-accent">{p.title}</h3>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
