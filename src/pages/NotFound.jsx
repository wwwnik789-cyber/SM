import { usePageMeta } from "../hooks/usePageMeta";
import { Btn } from "../components/ui/bits";
import { Marquee } from "../components/ui/motion";

export default function NotFound() {
  usePageMeta("404 — страница не найдена | SM-Production");
  return (
    <section className="flex min-h-svh flex-col items-center justify-center px-5 pt-24 text-center">
      <p className="text-outline display-h text-[26vw] font-black leading-none md:text-[16rem]">404</p>
      <h1 className="display-h mt-4 text-2xl font-bold md:text-3xl">Такой конструкции у нас нет… пока</h1>
      <p className="mt-4 max-w-md text-mut">Зато есть фотозоны, стенды и сцены любой сложности. Вернёмся на площадку?</p>
      <div className="mt-8 flex gap-4">
        <Btn to="/">На главную</Btn>
        <Btn to="/portfolio" variant="ghost">Портфолио</Btn>
      </div>
      <Marquee items={["404", "не найдено", "sm-production", "event · brand · decor"]} className="mt-16 w-full" />
    </section>
  );
}
