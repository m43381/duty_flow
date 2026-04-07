(function () {
    const STORAGE_KEY = "dutyflow-theme";
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function getSavedTheme() {
        return localStorage.getItem(STORAGE_KEY) || "system";
    }

    function resolveTheme(theme) {
        if (theme === "system") {
            return media.matches ? "dark" : "light";
        }
        return theme;
    }

    function applyTheme(theme) {
        const resolved = resolveTheme(theme);
        root.setAttribute("data-theme", resolved);
        root.setAttribute("data-theme-preference", theme);
        syncButtons(theme);
    }

    function saveTheme(theme) {
        localStorage.setItem(STORAGE_KEY, theme);
    }

    function syncButtons(theme) {
        document.querySelectorAll("[data-theme-value]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.themeValue === theme);
        });
    }

    function onThemeButtonClick(event) {
        const button = event.target.closest("[data-theme-value]");
        if (!button) return;

        const theme = button.dataset.themeValue;
        saveTheme(theme);
        applyTheme(theme);
    }

    function initThemeSwitcher() {
        const switcher = document.querySelector("[data-theme-switcher]");
        if (!switcher) return;

        switcher.addEventListener("click", onThemeButtonClick);
    }

    media.addEventListener("change", () => {
        const current = getSavedTheme();
        if (current === "system") {
            applyTheme(current);
        }
    });

    document.addEventListener("DOMContentLoaded", () => {
        applyTheme(getSavedTheme());
        initThemeSwitcher();
    });
})();