import { services } from "./services.js";
import { production } from "./production.js";
import { portfolio } from "./portfolio.js";
import { posts } from "./blog.js";
import { faq } from "./faq.js";
import { SITE } from "./site.js";

const staticRoutes = [
  {
    path: "/",
    title: "Оформление мероприятий под ключ | SM Production",
    description: "Застройка мероприятий, фотозоны, выставочные стенды, сцены и рекламные конструкции. Производство и монтаж в Москве и по России.",
    image: "/media/hero-stage.jpg",
    priority: 1,
    changefreq: "weekly",
    kind: "home",
  },
  {
    path: "/uslugi",
    title: "Услуги по оформлению мероприятий | SM Production",
    description: "Все услуги SM Production: застройка мероприятий, фотозоны, выставочные стенды, оформление сцен, рекламное производство, печать и монтаж.",
    image: "/media/hero-stage.jpg",
    priority: 0.95,
    changefreq: "weekly",
  },
  {
    path: "/proizvodstvo",
    title: "Рекламное производство на заказ | SM Production",
    description: "Изготовление вывесок, световых коробов, объёмных букв, стоек ресепшн, ростовых фигур и рекламных конструкций.",
    image: "/media/workshop.jpg",
    priority: 0.9,
    changefreq: "monthly",
  },
  {
    path: "/portfolio",
    title: "Портфолио оформления мероприятий | SM Production",
    description: "Реализованные проекты SM Production: застройка фестивалей и конференций, фотозоны, сцены, стенды и световые конструкции.",
    image: "/media/stand-festival.jpg",
    priority: 0.9,
    changefreq: "weekly",
  },
  {
    path: "/process",
    title: "Этапы работы над проектом | SM Production",
    description: "Как проходит работа: бриф, концепция, проектирование, производство, логистика, монтаж, сопровождение и демонтаж.",
    image: "/media/workshop.jpg",
    priority: 0.75,
    changefreq: "monthly",
  },
  {
    path: "/kalkulyator",
    title: "Калькулятор стоимости фотозоны | SM Production",
    description: "Рассчитайте ориентировочную стоимость фотозоны или press wall онлайн: размеры, материал, подсветка и дополнительные элементы.",
    image: "/media/photozone.jpg",
    priority: 0.8,
    changefreq: "monthly",
  },
  {
    path: "/arenda",
    title: "Аренда оборудования для мероприятий | SM Production",
    description: "Аренда света, звука, мебели и конструкций для мероприятий. Комплектация, доставка, монтаж и техническое сопровождение.",
    image: "/media/rental.jpg",
    priority: 0.75,
    changefreq: "monthly",
  },
  {
    path: "/media",
    title: "Видеопроизводство для бизнеса и событий | SM Media",
    description: "Студийная и выездная видеосъёмка, монтаж, графика и звук. Производство роликов для мероприятий, брендов и социальных сетей.",
    image: "/media/studio.jpg",
    priority: 0.7,
    changefreq: "monthly",
  },
  {
    path: "/b2b",
    title: "Производство для event-агентств и дизайнеров | SM Production",
    description: "Производственный партнёр для event-агентств: расчёты, проектная документация, производство, монтаж и прозрачная работа по договору.",
    image: "/media/workshop.jpg",
    priority: 0.75,
    changefreq: "monthly",
  },
  {
    path: "/o-kompanii",
    title: "О компании и производстве | SM Production",
    description: "SM Production проектирует, производит и монтирует декорации, стенды и рекламные конструкции для мероприятий и бизнеса.",
    image: "/media/workshop.jpg",
    priority: 0.65,
    changefreq: "yearly",
  },
  {
    path: "/team",
    title: "Команда и специалисты SM Production",
    description: "Дизайнеры, конструкторы, менеджеры проектов, производственные специалисты и монтажные бригады SM Production.",
    image: "/media/workshop.jpg",
    priority: 0.5,
    changefreq: "yearly",
  },
  {
    path: "/blog",
    title: "Блог об оформлении мероприятий | SM Production",
    description: "Практические материалы о фотозонах, выставочных стендах, сценах, печати, производстве декораций и работе на площадках.",
    image: "/media/hero-stage.jpg",
    priority: 0.75,
    changefreq: "weekly",
  },
  {
    path: "/otzyvy",
    title: "Отзывы клиентов | SM Production",
    description: "Отзывы заказчиков о производстве фотозон, стендов, сценического оформления и комплексной застройке мероприятий.",
    image: "/media/hero-stage.jpg",
    priority: 0.55,
    changefreq: "monthly",
  },
  {
    path: "/faq",
    title: "Вопросы об оформлении мероприятий | SM Production",
    description: "Ответы о сроках, материалах, стоимости, производстве, монтаже, аренде оборудования и подготовке макетов.",
    image: "/media/workshop.jpg",
    priority: 0.6,
    changefreq: "monthly",
    kind: "faq",
  },
  {
    path: "/materialy",
    title: "Материалы для декораций и рекламных конструкций",
    description: "ПВХ, акрил, баннер BlackBack, дерево, металл, композит, ткань и другие материалы для стендов, фотозон и вывесок.",
    image: "/media/workshop.jpg",
    priority: 0.6,
    changefreq: "monthly",
  },
  {
    path: "/vakansii",
    title: "Работа и вакансии в SM Production",
    description: "Работа в сфере рекламного и event-производства: актуальные вакансии для менеджеров, дизайнеров и производственных специалистов.",
    image: "/media/workshop.jpg",
    priority: 0.4,
    changefreq: "weekly",
  },
  {
    path: "/kontakty",
    title: "Контакты SM Production — Москва и Санкт-Петербург",
    description: "Телефон, почта и адреса SM Production в Москве и Санкт-Петербурге. Отправьте бриф для расчёта производства и монтажа.",
    image: "/media/workshop.jpg",
    priority: 0.8,
    changefreq: "yearly",
    kind: "contact",
  },
  {
    path: "/politika-konfidencialnosti",
    title: "Политика конфиденциальности | SM Production",
    description: "Политика обработки, использования и защиты персональных данных пользователей официального сайта SM Production.",
    priority: 0.2,
    changefreq: "yearly",
  },
  {
    path: "/karta-sayta",
    title: "Карта сайта | SM Production",
    description: "Карта официального сайта SM Production: основные разделы, услуги, направления производства, проекты, статьи и контакты.",
    priority: 0.3,
    changefreq: "monthly",
  },
];

function trimDescription(value, max = 158) {
  if (!value || value.length <= max) return value;
  return `${value.slice(0, max - 1).replace(/\s+\S*$/, "")}…`;
}

function fitTitle(value, suffix = " | SM Production", max = 68) {
  const full = `${value}${suffix}`;
  if (full.length <= max) return full;
  const available = max - suffix.length - 1;
  const shortened = value.slice(0, available).replace(/\s+\S*$/, "");
  return `${shortened}…${suffix}`;
}

function serviceRoutes() {
  return services.map((service) => ({
    path: `/uslugi/${service.slug}`,
    title: service.seoTitle,
    description: service.seoDescription,
    image: service.image,
    priority: 0.85,
    changefreq: "monthly",
    kind: "service",
    entity: service,
    parent: { name: "Услуги", path: "/uslugi" },
  }));
}

function productionRoutes() {
  return production.map((item) => ({
    path: `/proizvodstvo/${item.slug}`,
    title: `${item.title} на заказ | SM Production`,
    description: trimDescription(`${item.short} Проектирование, производство, доставка и монтаж.`),
    image: item.image,
    priority: 0.8,
    changefreq: "monthly",
    kind: "service",
    entity: item,
    parent: { name: "Производство", path: "/proizvodstvo" },
  }));
}

function portfolioRoutes() {
  return portfolio.map((item) => ({
    path: `/portfolio/${item.slug}`,
    title: `${item.title} — кейс | SM Production`,
    description: trimDescription(`${item.task} ${item.solution}`),
    image: item.image,
    priority: 0.7,
    changefreq: "yearly",
    kind: "case",
    entity: item,
    parent: { name: "Портфолио", path: "/portfolio" },
  }));
}

function blogRoutes() {
  return posts.map((post) => ({
    path: `/blog/${post.slug}`,
    title: fitTitle(post.title),
    description: trimDescription(post.excerpt),
    image: post.cover,
    priority: 0.65,
    changefreq: "yearly",
    kind: "article",
    entity: post,
    parent: { name: "Блог", path: "/blog" },
  }));
}

export function getSeoRoutes() {
  return [...staticRoutes, ...serviceRoutes(), ...productionRoutes(), ...portfolioRoutes(), ...blogRoutes()];
}

export function getSeoByPath(pathname) {
  const normalized = pathname === "/" ? "/" : pathname.replace(/\/$/, "");
  return getSeoRoutes().find((route) => route.path === normalized);
}

export function absoluteUrl(path = "/") {
  if (/^https?:\/\//.test(path)) return path;
  return `${SITE.url}${path.startsWith("/") ? path : `/${path}`}`;
}

export function buildStructuredData(meta) {
  const organization = {
    "@type": "Organization",
    "@id": `${SITE.url}/#organization`,
    name: SITE.name,
    url: SITE.url,
    logo: `${SITE.url}/favicon.svg`,
    telephone: SITE.phone,
    email: SITE.email,
    address: SITE.addresses,
  };
  const graph = [organization];

  if (meta.kind === "home") {
    graph.push({
      "@type": "WebSite",
      "@id": `${SITE.url}/#website`,
      name: SITE.name,
      url: SITE.url,
      inLanguage: "ru-RU",
      publisher: { "@id": `${SITE.url}/#organization` },
    });
  }
  if (meta.kind === "service") {
    graph.push({
      "@type": "Service",
      "@id": `${absoluteUrl(meta.path)}#service`,
      name: meta.entity.title,
      description: meta.description,
      url: absoluteUrl(meta.path),
      image: absoluteUrl(meta.image),
      provider: { "@id": `${SITE.url}/#organization` },
      areaServed: ["Москва", "Московская область", "Россия"],
    });
    if (meta.entity.faq?.length) {
      graph.push({
        "@type": "FAQPage",
        mainEntity: meta.entity.faq.map((item) => ({
          "@type": "Question",
          name: item.q,
          acceptedAnswer: { "@type": "Answer", text: item.a },
        })),
      });
    }
  }
  if (meta.kind === "article") {
    graph.push({
      "@type": "BlogPosting",
      headline: meta.entity.title,
      description: meta.description,
      image: absoluteUrl(meta.image),
      datePublished: meta.entity.date,
      dateModified: meta.entity.date,
      inLanguage: "ru-RU",
      mainEntityOfPage: absoluteUrl(meta.path),
      author: { "@id": `${SITE.url}/#organization` },
      publisher: { "@id": `${SITE.url}/#organization` },
    });
  }
  if (meta.kind === "case") {
    graph.push({
      "@type": "CreativeWork",
      name: meta.entity.title,
      description: meta.description,
      image: absoluteUrl(meta.image),
      url: absoluteUrl(meta.path),
      creator: { "@id": `${SITE.url}/#organization` },
      dateCreated: String(meta.entity.year),
    });
  }
  if (meta.kind === "faq") {
    graph.push({
      "@type": "FAQPage",
      mainEntity: faq.map((item) => ({
        "@type": "Question",
        name: item.q,
        acceptedAnswer: { "@type": "Answer", text: item.a },
      })),
    });
  }
  if (meta.kind === "contact") {
    graph.push({
      "@type": "ContactPage",
      name: meta.title,
      url: absoluteUrl(meta.path),
      mainEntity: { "@id": `${SITE.url}/#organization` },
    });
  }
  if (meta.parent) {
    graph.push({
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Главная", item: `${SITE.url}/` },
        { "@type": "ListItem", position: 2, name: meta.parent.name, item: absoluteUrl(meta.parent.path) },
        { "@type": "ListItem", position: 3, name: meta.entity.title, item: absoluteUrl(meta.path) },
      ],
    });
  }

  return { "@context": "https://schema.org", "@graph": graph };
}
