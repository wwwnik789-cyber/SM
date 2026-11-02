const S = (p) => ({
  width: p.size || 20,
  height: p.size || 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  className: p.className,
});

export const ArrowRight = (p) => (
  <svg {...S(p)}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></svg>
);
export const ArrowUpRight = (p) => (
  <svg {...S(p)}><path d="M7 17 17 7" /><path d="M8 7h9v9" /></svg>
);
export const ArrowLeft = (p) => (
  <svg {...S(p)}><path d="M19 12H5" /><path d="m11 18-6-6 6-6" /></svg>
);
export const Phone = (p) => (
  <svg {...S(p)}><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.8a2 2 0 0 1-.4 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.5 2.8.7a2 2 0 0 1 1.7 2Z" /></svg>
);
export const Mail = (p) => (
  <svg {...S(p)}><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-10 6L2 7" /></svg>
);
export const Send = (p) => (
  <svg {...S(p)}><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
);
export const Sun = (p) => (
  <svg {...S(p)}><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.9 4.9 1.4 1.4" /><path d="m17.7 17.7 1.4 1.4" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.3 17.7-1.4 1.4" /><path d="m19.1 4.9-1.4 1.4" /></svg>
);
export const Moon = (p) => (
  <svg {...S(p)}><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" /></svg>
);
export const Search = (p) => (
  <svg {...S(p)}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
);
export const Menu = (p) => (
  <svg {...S(p)}><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></svg>
);
export const Close = (p) => (
  <svg {...S(p)}><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
);
export const Check = (p) => (
  <svg {...S(p)}><path d="M20 6 9 17l-5-5" /></svg>
);
export const Plus = (p) => (
  <svg {...S(p)}><path d="M5 12h14" /><path d="M12 5v14" /></svg>
);
export const MapPin = (p) => (
  <svg {...S(p)}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></svg>
);
export const Clock = (p) => (
  <svg {...S(p)}><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
);
export const Spark = (p) => (
  <svg {...S(p)}><path d="M12 2 14.4 9.6 22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4Z" /></svg>
);
export const Ruler = (p) => (
  <svg {...S(p)}><path d="M21.3 8.7 15.3 2.7a1 1 0 0 0-1.4 0l-11.2 11.2a1 1 0 0 0 0 1.4l6 6a1 1 0 0 0 1.4 0l11.2-11.2a1 1 0 0 0 0-1.4Z" /><path d="m7.5 10.5 2 2" /><path d="m10.5 7.5 2 2" /><path d="m13.5 4.5 2 2" /></svg>
);
export const Factory = (p) => (
  <svg {...S(p)}><path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" /><path d="M17 18h1" /><path d="M12 18h1" /><path d="M7 18h1" /></svg>
);
export const Video = (p) => (
  <svg {...S(p)}><path d="m22 8-6 4 6 4V8Z" /><rect x="2" y="6" width="14" height="12" rx="2" /></svg>
);
export const Cube = (p) => (
  <svg {...S(p)}><path d="m21 16-9 5-9-5V8l9-5 9 5v8Z" /><path d="m3.3 8.7 8.7 4.8 8.7-4.8" /><path d="M12 22V13.5" /></svg>
);
export const Bolt = (p) => (
  <svg {...S(p)}><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" /></svg>
);
export const Star = (p) => (
  <svg {...S(p)} fill="currentColor" stroke="none"><path d="M12 2l2.9 6.6 7.1.7-5.4 4.8 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.3l7.1-.7L12 2z" /></svg>
);
export const Logo = ({ size = 34 }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <rect width="64" height="64" rx="14" fill="currentColor" opacity="0.08" />
    <rect x="4" y="4" width="56" height="56" rx="11" fill="none" stroke="var(--sm-accent)" strokeWidth="3" />
    <text x="32" y="42" fontFamily="Arial, sans-serif" fontSize="25" fontWeight="800" fill="currentColor" textAnchor="middle">SM</text>
    <circle cx="50" cy="14" r="4.5" fill="var(--sm-acid)" />
  </svg>
);
