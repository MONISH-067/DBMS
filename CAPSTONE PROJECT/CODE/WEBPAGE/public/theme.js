
(() => {
  const preference = window.matchMedia("(prefers-color-scheme: dark)");
  let saved;
  try { saved = localStorage.getItem("marketplace-theme"); } catch {}
  const apply = dark => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    const button = document.getElementById("theme-toggle");
    if (button) {
      button.setAttribute("aria-checked", String(dark));
      button.querySelector(".theme-label").textContent = dark ? "DARK" : "LIGHT";
      button.querySelector(".theme-knob").innerHTML = dark
        ? '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.5 8.5 0 1 0 20.5 14Z"/></svg>'
        : '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    }
  };
  apply(saved ? saved === "dark" : preference.matches);
  document.addEventListener("DOMContentLoaded", () => {
    apply(document.documentElement.dataset.theme === "dark");
    document.getElementById("theme-toggle").addEventListener("click", () => {
      const dark = document.documentElement.dataset.theme !== "dark";
      saved = dark ? "dark" : "light";
      apply(dark);
      try { localStorage.setItem("marketplace-theme", saved); } catch {}
    });
  });
  preference.addEventListener("change", event => { if (!saved) apply(event.matches); });
})();
