import fs from "node:fs/promises";
import path from "node:path";
import { getSeoRoutes, absoluteUrl } from "../src/data/seo.js";

const root = process.cwd();
const routes = getSeoRoutes();
const errors = [];
const warnings = [];
const seenPaths = new Set();
const seenTitles = new Set();
const seenDescriptions = new Set();

for (const route of routes) {
  if (seenPaths.has(route.path)) errors.push(`Duplicate path: ${route.path}`);
  if (seenTitles.has(route.title)) errors.push(`Duplicate title: ${route.title}`);
  if (seenDescriptions.has(route.description)) errors.push(`Duplicate description: ${route.path}`);
  seenPaths.add(route.path);
  seenTitles.add(route.title);
  seenDescriptions.add(route.description);

  if (route.title.length < 25 || route.title.length > 70) warnings.push(`Title ${route.title.length} chars: ${route.path}`);
  if (route.description.length < 90 || route.description.length > 165) warnings.push(`Description ${route.description.length} chars: ${route.path}`);
  if (!route.image && !["/politika-konfidencialnosti", "/karta-sayta"].includes(route.path)) warnings.push(`No explicit social image: ${route.path}`);

  const file = route.path === "/"
    ? path.join(root, "dist", "index.html")
    : path.join(root, "dist", route.path.slice(1), "index.html");
  let html = "";
  try {
    html = await fs.readFile(file, "utf8");
  } catch {
    errors.push(`Missing prerendered file: ${route.path}`);
    continue;
  }
  if (!html.includes(`<title>${route.title}</title>`)) errors.push(`Wrong title in HTML: ${route.path}`);
  if (!html.includes(`rel="canonical" href="${absoluteUrl(route.path)}"`)) errors.push(`Wrong canonical: ${route.path}`);
  if (!html.includes('id="page-structured-data"')) errors.push(`Missing JSON-LD: ${route.path}`);
  if (!html.includes("<h1")) errors.push(`Missing H1 in prerendered HTML: ${route.path}`);
  if (html.includes('<div id="root"></div>')) errors.push(`Empty prerendered body: ${route.path}`);
}

const sitemap = await fs.readFile(path.join(root, "dist", "sitemap.xml"), "utf8");
const sitemapCount = (sitemap.match(/<url>/g) || []).length;
if (sitemapCount !== routes.length) errors.push(`Sitemap has ${sitemapCount} URLs, expected ${routes.length}`);

warnings.forEach((warning) => console.warn(`WARN ${warning}`));
if (errors.length) {
  errors.forEach((error) => console.error(`ERR  ${error}`));
  process.exit(1);
}
console.log(`SEO validation passed: ${routes.length} routes, unique metadata, canonical URLs, JSON-LD and SSR HTML.`);
