# Логотипы SM Production
Список найденных версий логотипа на официальном сайте sm-production.ru:

| Файл               | Ссылка на оригинал                                                                                     | Назначение                  |
|--------------------|--------------------------------------------------------------------------------------------------------|-----------------------------|
| sm-logo-header.svg | https://static.tildacdn.com/tild3135-3438-4261-b438-646564646331/LOGO_SM__.svg                         | Логотип в шапке сайта       |
| sm-logo-medium.svg | https://static.tildacdn.com/tild3232-3063-4630-a431-653566613662/sm_logo-m.svg                         | Средняя версия логотипа     |
| sm-logo-small.svg  | https://static.tildacdn.com/tild3962-6165-4236-b330-306662623934/sm_logo-s.svg                         | Маленькая версия (футер/иконка) |
| sm-logo-main.svg   | https://static.tildacdn.com/tild3964-3163-4536-b530-343863313662/sm_logo.svg                         | Основная полноразмерная версия |

*Примечание: Прямая загрузка с CDN в песочнице временно заблокирована, ссылки на оригиналы сохранены. Когда вы предоставите логотипы в векторном/растровом формате мы их разместим в этой папке.*

## Социальные сети и площадки — один SVG

[**social-logos.svg**](../../public/media/social-logos.svg) — все девять логотипов в одном файле.

Файл хранится в `public/media/social-logos.svg`, поэтому Vite копирует его в сборку без дополнительного импорта. В запущенном приложении и после публикации он открывается по адресу **`/media/social-logos.svg`**.

Содержимое:

- сетка **3 × 3**, размер **960 × 720**, прозрачный фон;
- цветные векторные знаки с подписями; подписи переведены в кривые, установка шрифтов не требуется;
- без растровых вставок, скриптов и внешних ресурсов;
- каждый знак выделен в отдельный `<symbol>` без подписи, поэтому файл можно использовать и как готовый лист, и как SVG-спрайт.

| Логотип | ID символа | Источник векторного знака |
|---|---|---|
| ВКонтакте | `logo-vkontakte` | [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/vk.svg) |
| Pinterest | `logo-pinterest` | [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/pinterest.svg) |
| Telegram | `logo-telegram` | [gilbarbara/logos](https://github.com/gilbarbara/logos/blob/main/logos/telegram.svg) |
| Дзен | `logo-dzen` | [salute-developers/plasma](https://github.com/salute-developers/plasma/blob/dev/packages/sdds-icons/svg/36/DzenFill.svg) |
| YouTube | `logo-youtube` | [gilbarbara/logos](https://github.com/gilbarbara/logos/blob/main/logos/youtube-icon.svg) |
| RUTUBE | `logo-rutube` | [tsidukciya.github.io](https://github.com/tsidukciya/tsidukciya.github.io/blob/main/public/rutube.svg) |
| Яндекс Карты | `logo-yandex-maps` | [samarkand-guide](https://github.com/megahertz/samarkand-guide/blob/master/static/img/icons/yandex-maps.svg) |
| Яндекс Услуги | `logo-yandex-uslugi` | [webseed](https://github.com/romiro123/webseed/blob/main/src/img/svg/ya-uslugi.svg) |
| Авито | `logo-avito` | [effector](https://github.com/effector/effector/blob/master/documentation/public/logo/avito.svg), четырёхцветный знак без надписи |

Пример подключения отдельного знака (React, импорт файла не нужен):

```jsx
<svg width="32" height="32" viewBox="0 0 32 32" role="img" aria-label="ВКонтакте">
  <use href="/media/social-logos.svg#logo-vkontakte" width="32" height="32" />
</svg>
```

Для скачивания целого файла на сайте:

```html
<a href="/media/social-logos.svg" download="social-logos.svg">Скачать SVG с логотипами</a>
```

Подписи набраны DejaVu Sans и сохранены контурами; это поясняющие подписи, а не фирменные шрифтовые логотипы. При редактировании группы листа называются `tile-*`, подписи — `label-*`. Права на логотипы и товарные знаки принадлежат их владельцам.
