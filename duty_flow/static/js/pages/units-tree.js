(function () {
    function initUnitsTree() {
        const toggles = document.querySelectorAll("[data-unit-toggle]");
        const expandAllButton = document.querySelector("[data-tree-expand-all]");
        const collapseAllButton = document.querySelector("[data-tree-collapse-all]");
        const rows = document.querySelectorAll(".unit-tree__row[data-href]");

        function setExpanded(toggle, children, expanded) {
            children.classList.toggle("is-hidden", !expanded);
            toggle.classList.toggle("is-collapsed", !expanded);
            toggle.setAttribute("aria-expanded", String(expanded));
            toggle.textContent = expanded ? "▾" : "▸";
        }

        toggles.forEach((toggle) => {
            toggle.addEventListener("click", (event) => {
                event.stopPropagation();

                const node = toggle.closest("[data-unit-node]");
                if (!node) return;

                const children = node.querySelector("[data-unit-children]");
                if (!children) return;

                const expanded = children.classList.contains("is-hidden");
                setExpanded(toggle, children, expanded);
            });
        });

        if (expandAllButton) {
            expandAllButton.addEventListener("click", () => {
                toggles.forEach((toggle) => {
                    const node = toggle.closest("[data-unit-node]");
                    if (!node) return;
                    const children = node.querySelector("[data-unit-children]");
                    if (!children) return;
                    setExpanded(toggle, children, true);
                });
            });
        }

        if (collapseAllButton) {
            collapseAllButton.addEventListener("click", () => {
                toggles.forEach((toggle) => {
                    const node = toggle.closest("[data-unit-node]");
                    if (!node) return;
                    const children = node.querySelector("[data-unit-children]");
                    if (!children) return;
                    setExpanded(toggle, children, false);
                });
            });
        }

        rows.forEach((row) => {
            row.addEventListener("click", (event) => {
                const interactiveElement = event.target.closest("a, button, input, select, textarea, label");
                if (interactiveElement) return;

                const href = row.dataset.href;
                if (href) {
                    window.location.href = href;
                }
            });
        });
    }

    document.addEventListener("DOMContentLoaded", initUnitsTree);
})();