// SSR-рендер всех маршрутов: ловит ошибки времени выполнения без браузера.
const storage = () => {
  const m = new Map();
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v), removeItem: (k) => m.delete(k) };
};
globalThis.localStorage = storage();
globalThis.sessionStorage = storage();
globalThis.window = {
  addEventListener() {},
  removeEventListener() {},
  matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }),
  scrollTo() {},
  setTimeout: (...a) => setTimeout(...a),
  clearTimeout: (...a) => clearTimeout(...a),
  localStorage: globalThis.localStorage,
  sessionStorage: globalThis.sessionStorage,
};
globalThis.navigator ||= { userAgent: "node" };

const { createServer } = await import("vite");
const server = await createServer({ server: { middlewareMode: true }, appType: "custom", logLevel: "error" });

const React = (await import("react")).default;
const { renderToString } = await import("react-dom/server");
const { MemoryRouter } = await import("react-router-dom");
const { UIProvider } = await server.ssrLoadModule("/src/lib/store.jsx");
const { default: App } = await server.ssrLoadModule("/src/App.jsx");

const routes = [
  "/", "/uslugi", "/uslugi/fotozony", "/uslugi/akciya-fotozona", "/proizvodstvo", "/proizvodstvo/svetovye-vyveski",
  "/media", "/arenda", "/portfolio", "/portfolio/ctc-kids-vk-fest-2025", "/process", "/o-kompanii", "/team", "/b2b",
  "/blog", "/blog/trendy-oformleniya-meropriyatiy-2026", "/otzyvy", "/faq", "/kalkulyator", "/materialy", "/vakansii",
  "/kontakty", "/politika-konfidencialnosti", "/karta-sayta", "/definitely-missing-page",
];

let fail = 0;
for (const r of routes) {
  try {
    const html = renderToString(
      React.createElement(MemoryRouter, { initialEntries: [r] },
        React.createElement(UIProvider, null, React.createElement(App)))
    );
    const ok = html.length > 2000;
    console.log(`${ok ? "OK " : "SHORT"} ${r} (${html.length} chars)`);
    if (!ok) fail++;
  } catch (e) {
    fail++;
    console.log(`ERR ${r}: ${e.message.split("\n")[0]}`);
  }
}
await server.close();
process.exit(fail ? 1 : 0);
