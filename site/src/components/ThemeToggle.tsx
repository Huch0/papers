import { useEffect, useState } from "react";
export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    const d = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(d); document.documentElement.classList.toggle("dark", d);
  }, []);
  const toggle = () => {
    const d = !dark; setDark(d);
    document.documentElement.classList.toggle("dark", d);
    localStorage.setItem("theme", d ? "dark" : "light");
  };
  return (<button onClick={toggle} aria-label="Toggle dark mode" className="text-sm border rounded px-2 py-1">{dark ? "☀️" : "🌙"}</button>);
}
