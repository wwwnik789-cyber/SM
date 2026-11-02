import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { calcPhotozone, MATERIALS, OPTIONS, STANDARD_SIZES, STREET_STANDS } from "../lib/pricing";
import { fmtMoney } from "../lib/format";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Reveal } from "../components/ui/motion";
import { Btn } from "../components/ui/bits";
import { Ruler, Spark } from "../components/ui/Icons";
import { useUI } from "../lib/store";

function Preview({ w, h, material, options }) {
  const W = 320;
  const H = Math.max(90, (h / w) * W);
  const led = options.includes("light");
  const podium = options.includes("podium");
  const letters = options.includes("letters");
  const fill = material === "mirror" ? "url(#mirr)" : material === "fabric" ? "url(#fabr)" : "url(#bann)";
  return (
    <svg viewBox={`0 0 360 ${H + 90}`} className="w-full" role="img" aria-label="Предпросмотр фотозоны">
      <defs>
        <linearGradient id="bann" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#1c1c24" /><stop offset="1" stopColor="#101015" />
        </linearGradient>
        <linearGradient id="fabr" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#23232d" /><stop offset="1" stopColor="#14141a" />
        </linearGradient>
        <linearGradient id="mirr" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2a2a35" /><stop offset="0.5" stopColor="#0e0e13" /><stop offset="1" stopColor="#23232c" />
        </linearGradient>
      </defs>
      {/* floor */}
      <rect x="0" y={H + 30} width="360" height={H > 240 ? 55 : 40} fill="#0b0b10" />
      <line x1="0" y1={H + 30} x2="360" y2={H + 30} stroke="#26262f" strokeWidth="1" />
      {/* podium */}
      {podium && <rect x={20} y={H + 16} width="320" height="16" rx="3" fill="#15151c" stroke="#2c2c36" />}
      {/* frame */}
      <g transform={`translate(${(360 - W) / 2},20)`}>
        <rect x="-8" y="-8" width={W + 16} height={H + 16} rx="6" fill="#171720" />
        <rect x="0" y="0" width={W} height={H} rx="3" fill={fill} />
        {/* brand pattern */}
        {[...Array(6)].map((_, r) =>
          [...Array(4)].map((_, c) => (
            <circle key={r + "-" + c} cx={40 + c * 82} cy={26 + r * (H / 6)} r="7" fill="none" stroke="#ff4d1c" strokeOpacity="0.28" strokeWidth="2" />
          ))
        )}
        {led && <rect x="-4" y="-4" width={W + 8} height={H + 8} rx="5" fill="none" stroke="#d8ff3e" strokeWidth="3" style={{ filter: "drop-shadow(0 0 8px #d8ff3e)" }} />}
        {letters && (
          <text x={W / 2} y={H / 2 + 10} textAnchor="middle" fontFamily="Arial" fontWeight="900" fontSize={Math.min(44, H / 4)} fill="#f4f2ec" style={{ filter: "drop-shadow(0 0 10px #ff4d1c)" }}>
            ВАШ БРЕНД
          </text>
        )}
      </g>
      {/* human scale 170cm */}
      <g transform={`translate(24, ${H + 30 - (170 / h) * H})`} opacity="0.75">
        <circle cx="10" cy="6" r="6" fill="#98989f" />
        <rect x="4" y="14" width="12" height={(170 / h) * H - 20} rx="6" fill="#98989f" />
      </g>
      <text x="356" y={H + 52} textAnchor="end" fontFamily="monospace" fontSize="11" fill="#98989f">
        {w} × {h} см
      </text>
    </svg>
  );
}

export default function Calculator() {
  usePageMeta("Калькулятор стоимости фотозоны | SM-Production", "Рассчитайте предварительную стоимость фотозоны или пресс-волла онлайн: размеры, материалы, подсветка, срочность.");
  const [w, setW] = useState(300);
  const [h, setH] = useState(250);
  const [material, setMaterial] = useState("banner");
  const [options, setOptions] = useState(["light"]);
  const [urgent, setUrgent] = useState(false);
  const { openLead, notify } = useUI();

  const calc = useMemo(() => calcPhotozone({ w, h, material, options, urgent }), [w, h, material, options, urgent]);

  const toggle = (id) => setOptions((o) => (o.includes(id) ? o.filter((x) => x !== id) : [...o, id]));

  return (
    <>
      <PageHero overline="Инструмент" title={<>Калькулятор стоимости <span className="text-accent">фотозоны</span></>} text="Двигайте ползунки — предпросмотр и смета пересчитаются мгновенно. Финальную смету зафиксируем в договоре после консультации." />

      <section className="mx-auto max-w-7xl px-5">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          {/* controls */}
          <Reveal>
            <div className="space-y-8 rounded-3xl border border-line bg-card p-7 md:p-9">
              <div>
                <div className="flex items-center justify-between">
                  <label htmlFor="w" className="flex items-center gap-2 font-display text-sm font-bold"><Ruler size={15} className="text-accent" /> Ширина</label>
                  <span className="font-mono text-sm text-accent">{w} см</span>
                </div>
                <input id="w" type="range" min={100} max={1000} step={10} value={w} onChange={(e) => setW(+e.target.value)} className="mt-3 w-full" />
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <label htmlFor="h" className="flex items-center gap-2 font-display text-sm font-bold"><Ruler size={15} className="text-accent" /> Высота</label>
                  <span className="font-mono text-sm text-accent">{h} см</span>
                </div>
                <input id="h" type="range" min={100} max={500} step={10} value={h} onChange={(e) => setH(+e.target.value)} className="mt-3 w-full" />
              </div>

              <div>
                <p className="font-display text-sm font-bold">Материал</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {MATERIALS.map((m) => (
                    <button key={m.id} onClick={() => setMaterial(m.id)} className={`rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all ${material === m.id ? "border-accent bg-accent text-white" : "border-line text-mut hover:border-ink hover:text-ink"}`}>
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="font-display text-sm font-bold">Опции</p>
                <div className="mt-3 grid gap-2">
                  {OPTIONS.map((o) => (
                    <label key={o.id} className="flex cursor-pointer items-center justify-between rounded-xl border border-line px-4 py-3 transition-colors has-checked:border-acid">
                      <span className="flex items-center gap-3 text-sm font-semibold">
                        <input type="checkbox" checked={options.includes(o.id)} onChange={() => toggle(o.id)} className="h-4 w-4 accent-[var(--sm-acid)]" />
                        {o.label}
                      </span>
                      <span className="text-xs text-mut">+{fmtMoney(o.price)}</span>
                    </label>
                  ))}
                  <label className="flex cursor-pointer items-center justify-between rounded-xl border border-line px-4 py-3">
                    <span className="flex items-center gap-3 text-sm font-semibold">
                      <input type="checkbox" checked={urgent} onChange={(e) => setUrgent(e.target.checked)} className="h-4 w-4 accent-[var(--sm-accent)]" />
                      Срочное производство (×1,3)
                    </span>
                    <span className="text-xs text-accent">24–48 ч</span>
                  </label>
                </div>
              </div>
            </div>
          </Reveal>

          {/* preview + price */}
          <Reveal delay={0.1}>
            <div className="lg:sticky lg:top-28 space-y-5">
              <div className="rounded-3xl border border-line bg-bg2 p-6">
                <Preview w={w} h={h} material={material} options={options} />
              </div>
              <div className="rounded-3xl border border-line bg-card p-7">
                <div className="flex items-end justify-between">
                  <p className="font-display text-xs uppercase tracking-[0.24em] text-mut">Предварительно</p>
                  <AnimatePresence mode="popLayout">
                    <motion.p key={calc.total} initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -14, opacity: 0 }} className="display-h text-4xl font-black text-accent">
                      {fmtMoney(calc.total)}
                    </motion.p>
                  </AnimatePresence>
                </div>
                <dl className="mt-5 space-y-2.5 border-t border-line pt-5 text-sm">
                  <div className="flex justify-between"><dt className="text-mut">Площадь</dt><dd className="font-semibold">{calc.area} м²</dd></div>
                  <div className="flex justify-between"><dt className="text-mut">Каркас и печать</dt><dd className="font-semibold">{fmtMoney(calc.base)}</dd></div>
                  <div className="flex justify-between"><dt className="text-mut">Опции</dt><dd className="font-semibold">{fmtMoney(calc.extras)}</dd></div>
                </dl>
                <Btn onClick={() => { notify("Расчёт прикреплён к заявке"); openLead(`Фотозона ${w}×${h} см, ≈${fmtMoney(calc.total)}`); }} className="mt-6 w-full">
                  <Spark size={15} /> Отправить расчёт менеджеру
                </Btn>
                <p className="mt-3 text-center text-[11px] text-mut">Расчёт предварительный и не является публичной офертой</p>
              </div>
            </div>
          </Reveal>
        </div>

        {/* standard table */}
        <div className="mt-24">
          <h2 className="display-h mb-8 text-2xl font-bold md:text-3xl">Стандартные конструкции: цены</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {STANDARD_SIZES.map((s, i) => (
              <Reveal key={s.size} delay={(i % 3) * 0.05}>
                <button onClick={() => openLead(`Пресс-волл ${s.size}`)} className="card-hover w-full rounded-2xl border border-line bg-card p-6 text-left">
                  <div className="flex items-baseline justify-between">
                    <p className="display-h text-xl font-black">{s.size}</p>
                    <p className="font-display font-bold text-accent">{fmtMoney(s.price)}</p>
                  </div>
                  <p className="mt-2 text-sm text-mut">{s.label} · {s.use}</p>
                  <p className="mt-3 text-xs font-semibold text-accent">В цене: каркас, печать, монтаж и демонтаж →</p>
                </button>
              </Reveal>
            ))}
          </div>
        </div>

        <div className="mt-16">
          <h2 className="display-h mb-8 text-2xl font-bold md:text-3xl">Уличные стенды</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {STREET_STANDS.map((s, i) => (
              <Reveal key={s.size} delay={i * 0.07}>
                <button onClick={() => openLead(`Уличный стенд ${s.size}`)} className="card-hover w-full rounded-2xl border border-line bg-bg2 p-6 text-left">
                  <p className="display-h text-lg font-black">{s.size}</p>
                  <p className="mt-1 text-sm text-mut">{s.note}</p>
                  <p className="mt-3 font-display font-bold text-accent">от {fmtMoney(s.price)}</p>
                </button>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
