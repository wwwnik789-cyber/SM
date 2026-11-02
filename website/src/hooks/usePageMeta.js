import { useEffect } from "react";
import { SITE } from "../data/site";
import { buildStructuredData, getSeoByPath } from "../data/seo";

export const SITE_URL = SITE.url;
export const DEFAULT_IMAGE = `${SITE.url}${SITE.defaultImage}`;
export const SITE_NAME = SITE.name;

function upsertMeta(selector, attributes, content) {
  let element = document.head.querySelector(selector);
  if (!element) {
    element = document.createElement("meta");
    Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
    document.head.appendChild(element);
  }
  element.setAttribute("content", content);
}

function upsertLink(rel, href) {
  let element = document.head.querySelector(`link[rel="${rel}"]`);
  if (!element) {
    element = document.createElement("link");
    element.setAttribute("rel", rel);
    document.head.appendChild(element);
  }
  element.setAttribute("href", href);
}

function absoluteUrl(value, fallback = SITE_URL) {
  if (!value) return fallback;
  if (/^https?:\/\//.test(value)) return value;
  return `${SITE_URL}${value.startsWith("/") ? value : `/${value}`}`;
}

export function usePageMeta(input, legacyDescription) {
  const isLegacy = typeof input === "string";
  const explicit = isLegacy
    ? { title: input, description: legacyDescription }
    : (input || {});
  const currentPath = explicit.path || (typeof window !== "undefined" ? window.location.pathname : null);
  const routeMeta = currentPath ? getSeoByPath(currentPath) : null;
  const automaticSchema = routeMeta
    ? buildStructuredData(routeMeta)["@graph"].filter((item) => item["@id"] !== `${SITE_URL}/#organization`)
    : [];
  const options = {
    ...(isLegacy ? explicit : routeMeta || {}),
    ...(isLegacy ? routeMeta || {} : explicit),
    schema: explicit.schema ?? automaticSchema,
  };
  const signature = JSON.stringify(options);

  useEffect(() => {
    const {
      title,
      description = "SM Production — проектирование, производство и монтаж оформления для мероприятий, выставок и бизнеса.",
      path = window.location.pathname,
      image = DEFAULT_IMAGE,
      type = "website",
      noindex = false,
      schema = [],
    } = options;

    const canonical = absoluteUrl(path === "/" ? "/" : path.replace(/\/$/, ""));
    const socialImage = absoluteUrl(image, DEFAULT_IMAGE);
    document.documentElement.lang = "ru";
    if (title) document.title = title;

    upsertMeta('meta[name="description"]', { name: "description" }, description);
    upsertMeta('meta[name="robots"]', { name: "robots" }, noindex ? "noindex,nofollow" : "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1");
    upsertMeta('meta[property="og:type"]', { property: "og:type" }, type);
    upsertMeta('meta[property="og:locale"]', { property: "og:locale" }, "ru_RU");
    upsertMeta('meta[property="og:site_name"]', { property: "og:site_name" }, SITE_NAME);
    upsertMeta('meta[property="og:title"]', { property: "og:title" }, title || SITE_NAME);
    upsertMeta('meta[property="og:description"]', { property: "og:description" }, description);
    upsertMeta('meta[property="og:url"]', { property: "og:url" }, canonical);
    upsertMeta('meta[property="og:image"]', { property: "og:image" }, socialImage);
    upsertMeta('meta[property="og:image:alt"]', { property: "og:image:alt" }, title || SITE_NAME);
    upsertMeta('meta[name="twitter:card"]', { name: "twitter:card" }, "summary_large_image");
    upsertMeta('meta[name="twitter:title"]', { name: "twitter:title" }, title || SITE_NAME);
    upsertMeta('meta[name="twitter:description"]', { name: "twitter:description" }, description);
    upsertMeta('meta[name="twitter:image"]', { name: "twitter:image" }, socialImage);
    upsertLink("canonical", canonical);

    let script = document.head.querySelector("#page-structured-data");
    if (!script) {
      script = document.createElement("script");
      script.id = "page-structured-data";
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }
    const baseSchema = {
      "@context": "https://schema.org",
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: SITE_NAME,
      url: SITE_URL,
      logo: `${SITE_URL}/favicon.svg`,
      telephone: SITE.phone,
      email: SITE.email,
      address: SITE.addresses,
    };
    const items = [baseSchema, ...(Array.isArray(schema) ? schema : [schema]).filter(Boolean)];
    script.textContent = JSON.stringify(items.length === 1 ? items[0] : { "@context": "https://schema.org", "@graph": items.map(({ "@context": _, ...item }) => item) });
  }, [signature]);
}

export function useLockBody(locked) {
  useEffect(() => {
    if (!locked) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [locked]);
}
