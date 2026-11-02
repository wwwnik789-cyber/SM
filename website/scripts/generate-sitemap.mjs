import fs from "node:fs/promises";
import { getSeoRoutes, absoluteUrl } from "../src/data/seo.js";

const routes = getSeoRoutes();
const today = new Date().toISOString().slice(0, 10);
const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes.map((route) => `  <url><loc>${absoluteUrl(route.path)}</loc><lastmod>${today}</lastmod><changefreq>${route.changefreq}</changefreq><priority>${route.priority}</priority></url>`).join("\n")}
</urlset>\n`;
await fs.writeFile(new URL("../public/sitemap.xml", import.meta.url), xml);
console.log(`Generated sitemap.xml with ${routes.length} URLs.`);
