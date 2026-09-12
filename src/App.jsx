import { useEffect, useLayoutEffect, useRef } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import { BackToTop, CookieBanner, CursorGlow, Preloader, ScrollProgress, Toast } from "./components/layout/chrome";
import { CommandPalette, LeadModal } from "./components/layout/overlays";

import Home from "./pages/Home";
import Services from "./pages/Services";
import ServiceDetail from "./pages/ServiceDetail";
import Production from "./pages/Production";
import ProductionDetail from "./pages/ProductionDetail";
import Media from "./pages/Media";
import Rental from "./pages/Rental";
import Portfolio from "./pages/Portfolio";
import PortfolioDetail from "./pages/PortfolioDetail";
import Process from "./pages/Process";
import About from "./pages/About";
import Team from "./pages/Team";
import B2B from "./pages/B2B";
import Blog from "./pages/Blog";
import BlogPost from "./pages/BlogPost";
import Reviews from "./pages/Reviews";
import Faq from "./pages/Faq";
import Calculator from "./pages/Calculator";
import Materials from "./pages/Materials";
import Careers from "./pages/Careers";
import Contacts from "./pages/Contacts";
import Privacy from "./pages/Privacy";
import Sitemap from "./pages/Sitemap";
import NotFound from "./pages/NotFound";

function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useLayoutEffect(() => {
    if (!hash) window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname, hash]);
  return null;
}

/* «Перелистывание» страницы: акцентная шторка проходит по экрану при смене маршрута */
function RouteCurtain() {
  const location = useLocation();
  const reduce = useReducedMotion();
  const first = useRef(true);
  useEffect(() => {
    first.current = false;
  }, []);
  if (reduce || first.current) return null;
  return (
    <motion.div
      key={location.pathname}
      className="pointer-events-none fixed inset-0 z-[96] flex"
      initial="hidden"
      animate="show"
      aria-hidden="true"
    >
      {[0, 1, 2, 3].map((i) => (
        <motion.span
          key={i}
          variants={{
            hidden: { scaleY: 0 },
            show: {
              scaleY: [0, 1, 1, 0],
              transformOrigin: ["top", "top", "bottom", "bottom"],
              transition: { duration: 0.9, times: [0, 0.38, 0.62, 1], delay: i * 0.05, ease: [0.7, 0, 0.25, 1] },
            },
          }}
          className={`h-full flex-1 ${i % 2 ? "bg-accent" : "bg-bg2"}`}
        />
      ))}
    </motion.div>
  );
}

function Page({ children }) {
  const reduce = useReducedMotion();
  return (
    <motion.main
      initial={{ opacity: 0, y: reduce ? 0 : 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: reduce ? 0 : -12 }}
      transition={{ duration: 0.45, ease: [0.2, 0.65, 0.25, 1] }}
    >
      {children}
    </motion.main>
  );
}

export default function App() {
  const location = useLocation();
  return (
    <div className="noise relative">
      <ScrollToTop />
      <ScrollProgress />
      <CursorGlow />
      <Header />
      <RouteCurtain />
      <AnimatePresence mode="wait" initial={false}>
        <Page key={location.pathname}>
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/uslugi" element={<Services />} />
            <Route path="/uslugi/:slug" element={<ServiceDetail />} />
            <Route path="/proizvodstvo" element={<Production />} />
            <Route path="/proizvodstvo/:slug" element={<ProductionDetail />} />
            <Route path="/media" element={<Media />} />
            <Route path="/arenda" element={<Rental />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/portfolio/:slug" element={<PortfolioDetail />} />
            <Route path="/process" element={<Process />} />
            <Route path="/o-kompanii" element={<About />} />
            <Route path="/team" element={<Team />} />
            <Route path="/b2b" element={<B2B />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route path="/otzyvy" element={<Reviews />} />
            <Route path="/faq" element={<Faq />} />
            <Route path="/kalkulyator" element={<Calculator />} />
            <Route path="/materialy" element={<Materials />} />
            <Route path="/vakansii" element={<Careers />} />
            <Route path="/kontakty" element={<Contacts />} />
            <Route path="/politika-konfidencialnosti" element={<Privacy />} />
            <Route path="/karta-sayta" element={<Sitemap />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Page>
      </AnimatePresence>
      <Footer />
      <LeadModal />
      <CommandPalette />
      <Toast />
      <CookieBanner />
      <BackToTop />
      <Preloader />
    </div>
  );
}
