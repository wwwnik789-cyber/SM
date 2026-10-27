# Микроразметка Schema.org (JSON-LD) — готовые блоки кода
**Дата:** 15.10.2026 · Тариф **Personal** подходит: вставка HTML-кода в Tilda доступна на платных тарифах (Personal и Business); Business отличается от Personal только экспортом исходного кода и числом сайтов.

## Куда вставлять

**Способ 1 — на всю страницу (рекомендуется):** «Страницы» → нужная страница → «Настройки страницы» → вкладка **Дополнительно** → «HTML-код для вставки внутрь HEAD».

**Способ 2 — блоком на странице:** добавить блок **T123 «HTML-код»** (раздел «Другое») и вставить код в него. Подходит, если нужно добавить разметку в конкретное место (например, FAQ-аккордеон).

**Про Tilda Store:** Tilda автоматически добавляет микроразметку товара для карточек каталога. Наша задача — проверить, что именно она отдаёт, и добить недостающие поля (`brand`, `sku`, `review`, `aggregateRating`, `additionalProperty`). Проверка: `validator.schema.org`, «Инструменты → Проверка структурированных данных» в Яндекс Вебмастере, Rich Results Test в Google Search Console.

---

## 1. Organization + LocalBusiness — на все страницы (в HEAD сайта)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": ["Organization", "LocalBusiness", "Store"],
  "@id": "https://bakmasters.su/#organization",
  "name": "BAK MASTERS",
  "alternateName": "Бак Мастерс",
  "description": "Мастерская изделий ручной работы из ценных пород дерева и эпоксидной смолы: столики, чабани, кухонные борды, подсвечники. Москва, доставка по России.",
  "url": "https://bakmasters.su/",
  "logo": "https://bakmasters.su/logo.png",
  "image": "https://bakmasters.su/og-image.jpg",
  "telephone": "+79261609110",
  "email": "bak.masters@yandex.ru",
  "priceRange": "2990-30000 RUB",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Москва",
    "addressCountry": "RU",
    "streetAddress": "⚠️ указать адрес или удалить поле streetAddress"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "⚠️ 55.7558",
    "longitude": "⚠️ 37.6173"
  },
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    "opens": "10:00",
    "closes": "20:00"
  },
  "sameAs": [
    "https://vk.com/bak_mast",
    "https://t.me/bak_masters_workshop",
    "https://wa.me/79261609110"
  ],
  "areaServed": {
    "@type": "Country",
    "name": "Россия"
  },
  "paymentAccepted": "⚠️ СБП, банковский перевод, наличные",
  "currenciesAccepted": "RUB"
}
</script>
```

⚠️ **Важно про `openingHours` и `address`:** нельзя писать в разметке данные, которых нет на сайте или которые не соответствуют реальности. Несовпадение разметки и фактов — причина понижения в выдаче и снятия расширенных сниппетов. Заполняйте только то, что подтверждено.

⚠️ **`logo` и `image`:** нужны реальные URL файлов, загруженных в Tilda (логотип квадратный ≥ 112×112 px, og-изображение 1200×630 px). Сейчас на сайте логотип — SVG (`-1_1_Traced.svg`), а для разметки и соцсетей надёжнее PNG/JPG.

---

## 2. WebSite + поиск по сайту — на главную

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://bakmasters.su/#website",
  "url": "https://bakmasters.su/",
  "name": "BAK MASTERS",
  "publisher": { "@id": "https://bakmasters.su/#organization" },
  "inLanguage": "ru-RU"
}
</script>
```

`potentialAction` с `SearchAction` добавляйте только после того, как на сайте появится рабочая строка поиска по магазину (сейчас её нет).

---

## 3. Product + Offer — шаблон для карточки товара

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Придвижной столик МАЙГОТО (абрикос)",
  "image": [
    "https://bakmasters.su/photo1.jpg",
    "https://bakmasters.su/photo2.jpg"
  ],
  "description": "Придвижной столик из спилов южного абрикоса с эпоксидной смолой. Столешница пропитана маслами и восками, подстолье — металл с порошковой краской. Размеры 330×330×610 мм.",
  "sku": "⚠️ BM-MAIGOTO-ABR",
  "mpn": "⚠️ optional",
  "brand": { "@type": "Brand", "name": "BAK MASTERS" },
  "category": "Придвижные столики",
  "material": ["Абрикос", "Эпоксидная смола", "Металл"],
  "color": "Персиковый / прозрачная смола",
  "additionalProperty": [
    { "@type": "PropertyValue", "name": "Длина, мм", "value": "330" },
    { "@type": "PropertyValue", "name": "Ширина, мм", "value": "330" },
    { "@type": "PropertyValue", "name": "Высота, мм", "value": "610" },
    { "@type": "PropertyValue", "name": "Покрытие", "value": "Масло и воск" },
    { "@type": "PropertyValue", "name": "Изготовление", "value": "Ручная работа" }
  ],
  "offers": {
    "@type": "Offer",
    "url": "https://bakmasters.su/shop/tproduct/434391513-458287002081-maigoto-abrikos",
    "priceCurrency": "RUB",
    "price": "26900",
    "priceValidUntil": "2027-12-31",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingRate": { "@type": "MonetaryAmount", "value": "0", "currency": "RUB" },
      "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "RU" },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": { "@type": "QuantitativeValue", "minValue": 1, "maxValue": 2, "unitCode": "d" },
        "transitTime": { "@type": "QuantitativeValue", "minValue": 2, "maxValue": 7, "unitCode": "d" }
      }
    },
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "RU",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 7,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/ReturnFeesCustomerResponsibility"
    }
  }
}
</script>
```

⚠️ **Ключевые моменты:**
- `availability`: `InStock` для изделий в наличии, `MadeToOrder`/`PreOrder` для позиций «под заказ», `OutOfStock` если закончилось. Нельзя ставить `InStock` на то, чего нет, — Google и Яндекс это наказывают.
- `price` — числом, без пробелов и символа ₽.
- `merchantReturnDays: 7` — соответствует ст. 26.1 ЗоЗПП для дистанционной продажи. Для изделий по индивидуальному заказу укажите `MerchantReturnNotPermitted` в отдельной разметке этой карточки.
- `aggregateRating` и `review` добавляйте **только при наличии реальных отзывов**. Пустая или выдуманная разметка рейтинга — прямой путь к санкциям.

Шаблон для отзывов (добавлять внутрь `Product`):

```html
"aggregateRating": {
  "@type": "AggregateRating",
  "ratingValue": "4.9",
  "reviewCount": "12",
  "bestRating": "5",
  "worstRating": "1"
},
"review": [{
  "@type": "Review",
  "author": { "@type": "Person", "name": "Анна" },
  "datePublished": "2026-09-14",
  "reviewBody": "Столик МАЙГОТО — огонь. Стоит у дивана, ноутбук и чай всегда под рукой. Дерево тёплое на ощупь, смолы совсем не видно на стыках.",
  "reviewRating": { "@type": "Rating", "ratingValue": "5", "bestRating": "5" }
}]
```

---

## 4. BreadcrumbList — хлебные крошки

Добавлять на все внутренние страницы: каталог, категории, карточки товаров, `/toorder`, `/aboutus`, `/faq`, `/dostavka-i-oplata`.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://bakmasters.su/" },
    { "@type": "ListItem", "position": 2, "name": "Каталог", "item": "https://bakmasters.su/shop" },
    { "@type": "ListItem", "position": 3, "name": "Придвижные столики", "item": "https://bakmasters.su/catalog/pridvizhnye-stoliki" },
    { "@type": "ListItem", "position": 4, "name": "МАЙГОТО абрикос" }
  ]
}
</script>
```

⚠️ Хлебные крошки должны быть **видны на странице**, а не только в разметке — иначе это нарушение рекомендаций поисковиков. В Tilda есть блоки хлебных крошек; если их нет — добавить текстовую строку в начале страницы.

---

## 5. FAQPage — для `/faq`, `/sotrudnichestvo`, страниц категорий и блоков FAQ на главной

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Изделие будет точно таким же, как на фото?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Нет, и это главное отличие ручной работы. Каждое изделие делается из конкретного спила: рисунок дерева и переходы смолы всегда разные. Перед отправкой присылаем фото именно вашего изделия."
      }
    },
    {
      "@type": "Question",
      "name": "Сколько времени занимает индивидуальный заказ?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "В среднем 10–20 дней: подготовка древесины, послойная заливка, многоэтапная шлифовка и пропитка маслом."
      }
    },
    {
      "@type": "Question",
      "name": "Сколько стоит доставка?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "До ПВЗ СДЭК по России — бесплатно при весе до 25 кг и объёме до 0,1 м³. По Москве и области — курьер день в день по тарифу Яндекс Доставки."
      }
    },
    {
      "@type": "Question",
      "name": "Можно ли заказать другой размер или оттенок смолы?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Да, при индивидуальном заказе возможен любой оттенок заливки и размер в пределах технологических ограничений."
      }
    },
    {
      "@type": "Question",
      "name": "Нужна ли предоплата?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Да: 50% при заказе свыше 10 000 ₽ и 100% при заказе до 10 000 ₽. Остаток — после фото готового изделия, до отправки."
      }
    }
  ]
}
</script>
```

⚠️ Текст в разметке должен совпадать с текстом, видимым на странице. Вопросы и ответы — копировать из `tilda/04-faq.md`.

⚠️ Google с 2023 года показывает FAQ-сниппеты преимущественно для крупных авторитетных и государственных сайтов, поэтому визуально расширенного сниппета в Google может не быть. В Яндексе FAQ-разметка по-прежнему работает — это основной ориентир для российского трафика.

---

## 6. ItemList — для страниц категорий и каталога

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Подсвечники из дерева и эпоксидной смолы",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "url": "https://bakmasters.su/shop/tproduct/434391513-139903145691-kanoa", "name": "Подсвечник КАНОА" },
    { "@type": "ListItem", "position": 2, "url": "https://bakmasters.su/shop/tproduct/434391513-236449433161-psedona", "name": "Подсвечник ПСЕДОНА" }
  ]
}
</script>
```

---

## 7. Чек-лист внедрения

- [ ] Organization/LocalBusiness — в HEAD всех страниц (один раз, глобально, через «Настройки сайта» или на каждой странице)
- [ ] WebSite — на главной
- [ ] Product + Offer — на всех 36 карточках (проверить, что отдаёт Tilda, и добить поля)
- [ ] BreadcrumbList — на всех внутренних страницах + видимые хлебные крошки
- [ ] FAQPage — на `/faq`, на `/sotrudnichestvo`, на 12 посадочных категорий, в блоке FAQ на главной
- [ ] ItemList — на страницах категорий
- [ ] AggregateRating / Review — **после** сбора настоящих отзывов
- [ ] Проверить всё в `validator.schema.org` и в Яндекс Вебмастере → «Инструменты → Проверка структурированных данных»
- [ ] После переезда на `.ru` заменить домен во всех URL разметки (это десятки мест — держать список)
