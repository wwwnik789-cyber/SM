import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const Ctx = createContext(null);

const THEME_KEY = "sm-theme";

export function UIProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "dark";
    return localStorage.getItem(THEME_KEY) || "dark";
  });
  const [leadOpen, setLeadOpen] = useState(false);
  const [leadTopic, setLeadTopic] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);

  const openLead = useCallback((topic = "") => {
    setLeadTopic(topic);
    setLeadOpen(true);
  }, []);

  const notify = useCallback((msg) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 3800);
  }, []);

  // Ctrl/Cmd+K — command palette
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if (e.key === "Escape") {
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const value = useMemo(
    () => ({ theme, toggleTheme, leadOpen, setLeadOpen, leadTopic, openLead, paletteOpen, setPaletteOpen, toast, notify }),
    [theme, toggleTheme, leadOpen, leadTopic, openLead, paletteOpen, toast, notify]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useUI = () => useContext(Ctx);
