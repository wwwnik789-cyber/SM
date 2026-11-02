import fs from "node:fs/promises";
import path from "node:path";
import React from "react";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { createServer } from "vite";

const root = process.cwd();
const dist = path.join(root, "dist");

const storage = () => {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
};
globalThis.localStorage = storage();
globalThis.sessionStorage = storage();
globalThis.window = {
  addEventListener() {},
  removeEventListener() {},
  matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }),
  scrollTo() {},
  setTimeout: (...args) => setTimeout(...args),
  clearTimeout: (...args) => clearTimeout(...args),
  localStorage: globalThis.localStorage,
  sessionStorage: globalThis.sessionStorage,
  location: { pathname: "/" },
};
globalThis.navigator ||= { userAgent: "node" };

const server = await createServer({
  root,
  server: { middlewareMode: true },
  appType: "custom",
  logLevel: "error",
});

const { UIProvider } = await server.ssrLoadModule("/src/lib/store.jsx");
const { default: App } = await server.ssrLoadModule("/src/App.jsx");
const { getSeoRoutes, absoluteUrl, buildStructuredData } = await server.ssrLoadModule("/src/data/seo.js");
const { SITE } = await server.ssrLoadModule("/src/data/site.js");
const routes = getSeoRoutes();
const template = await fs.readFile(path.join(dist, "index.html"), "utf8");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function cleanHead(html) {
  return html
    .replace(/\s*<title>[\s\S]*?<\/title>/gi, "")
    .replace(/\s*<meta\b[^>]*(?:name|property)=["'](?:description|robots|og:[^"']+|twitter:[^"']+)["'][^>]*>/gi, "")
    .replace(/\s*<link\b[^>]*rel=["']canonical["'][^>]*>/gi, "")
    .replace(/\s*<script\b[^>]*type=["']application\/ld\+json["'][^>]*>[\s\S]*?<\/script>/gi, "");
}

function pageHead(meta) {
  const canonical = absoluteUrl(meta.path);
  const image = absoluteUrl(meta.image || SITE.defaultImage);
  const structured = JSON.stringify(buildStructuredData(meta)).replaceAll("<", "\\u003c");
  const title = escapeHtml(meta.title);
  const description = escapeHtml(meta.description);
  return `
    <title>${title}</title>
    <meta name="description" content="${description}" />
    <meta name="robots" content="${meta.noindex ? "noindex,nofollow" : "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"}" />
    <link rel="canonical" href="${canonical}" />
    <meta property="og:type" content="${meta.kind === "article" ? "article" : "website"}" />
    <meta property="og:locale" content="ru_RU" />
    <meta property="og:site_name" content="${escapeHtml(SITE.name)}" />
    <meta property="og:title" content="${title}" />
    <meta property="og:description" content="${description}" />
    <meta property="og:url" content="${canonical}" />
    <meta property="og:image" content="${image}" />
    <meta property="og:image:alt" content="${title}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${title}" />
    <meta name="twitter:description" content="${description}" />
    <meta name="twitter:image" content="${image}" />
    <script id="page-structured-data" type="application/ld+json">${structured}</script>`;
}

const base = cleanHead(template);
for (const meta of routes) {
  window.location.pathname = meta.path;
  const body = renderToString(
    React.createElement(
      MemoryRouter,
      { initialEntries: [meta.path] },
      React.createElement(UIProvider, null, React.createElement(App)),
    ),
  );
  const html = base
    .replace("</head>", `${pageHead(meta)}\n  </head>`)
    .replace('<div id="root"></div>', `<div id="root">${body}</div>`);
  if (meta.path === "/") {
    await fs.writeFile(path.join(dist, "index.html"), html);
  } else {
    const directoryTarget = path.join(dist, meta.path.slice(1), "index.html");
    const cleanUrlTarget = path.join(dist, `${meta.path.slice(1)}.html`);
    await fs.mkdir(path.dirname(directoryTarget), { recursive: true });
    await fs.mkdir(path.dirname(cleanUrlTarget), { recursive: true });
    await fs.writeFile(directoryTarget, html);
    await fs.writeFile(cleanUrlTarget, html);
  }
}

const notFoundMeta = {
  path: "/404",
  title: "404 — страница не найдена | SM Production",
  description: "Запрошенная страница не найдена. Перейдите в каталог услуг или вернитесь на главную страницу SM Production.",
  noindex: true,
};
window.location.pathname = "/404";
const notFoundBody = renderToString(
  React.createElement(
    MemoryRouter,
    { initialEntries: ["/404"] },
    React.createElement(UIProvider, null, React.createElement(App)),
  ),
);
const notFoundHtml = base
  .replace("</head>", `${pageHead(notFoundMeta)}\n  </head>`)
  .replace('<div id="root"></div>', `<div id="root">${notFoundBody}</div>`);
await fs.writeFile(path.join(dist, "404.html"), notFoundHtml);

const today = new Date().toISOString().slice(0, 10);
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes.map((route) => `  <url><loc>${absoluteUrl(route.path)}</loc><lastmod>${today}</lastmod><changefreq>${route.changefreq}</changefreq><priority>${route.priority}</priority></url>`).join("\n")}
</urlset>\n`;
await fs.writeFile(path.join(dist, "sitemap.xml"), sitemap);
await server.close();
console.log(`Prerendered ${routes.length} indexable routes.`);
