import { useMemo, useState } from "react";
import { faq } from "../data/faq";
import { usePageMeta } from "../hooks/usePageMeta";
import PageHero from "../components/ui/PageHero";
import { Accordion, Btn } from "../components/ui/bits";
import { Search } from "../components/ui/Icons";
import { useUI } from "../lib/store";

export default function Faq() {
  usePageMeta("Вопросы и ответы | SM-Production", "Часто задаваемые вопросы об оформлении мероприятий, сроках, материалах и аренде оборудования.");
  const [q, setQ] = useState("");
  const { openLead } = useUI();
  const list = useMemo(() => (q.trim() ? faq.filter((f) => (f.q + f.a).toLowerCase().includes(q.toLowerCase())) : faq), [q]);

  return (
    <>
      <PageHero overline="FAQ" title={<>Вопросы — <span className="text-accent">ответы</span></>} text="Собрали всё, что чаще всего спрашивают перед заказом. Не нашли ответ — напишите нам, отвечаем быстро.">
        <label className="mt-8 flex w-full max-w-md items-center gap-3 rounded-2xl border border-line bg-card px-5 py-4">
          <Search size={17} className="text-mut" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Найти вопрос…" className="w-full bg-transparent outline-none" />
        </label>
      </PageHero>

      <section className="mx-auto max-w-4xl px-5">
        {list.length ? <Accordion items={list} /> : <p className="py-16 text-center text-mut">По «{q}» ничего нет. Задайте вопрос напрямую — мы на связи 24/7.</p>}
        <div className="mt-14 rounded-3xl border border-line bg-card p-8 text-center">
          <h2 className="display-h text-2xl font-bold">Остались вопросы?</h2>
          <p className="mt-2 text-mut">Свяжитесь с нами и получите профессиональную консультацию.</p>
          <div className="mt-6 flex justify-center gap-4">
            <Btn onClick={() => openLead("Вопрос")}>Задать вопрос</Btn>
            <Btn to="/kontakty" variant="ghost">Контакты</Btn>
          </div>
        </div>
      </section>
    </>
  );
}
