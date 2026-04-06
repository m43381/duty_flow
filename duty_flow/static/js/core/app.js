(function () {
    function initSidebar() {
        const sidebar = document.querySelector("[data-sidebar]");
        const toggle = document.querySelector("[data-sidebar-toggle]");
        const backdrop = document.querySelector("[data-sidebar-backdrop]");

        if (!sidebar || !toggle || !backdrop) return;

        function openSidebar() {
            sidebar.classList.add("is-open");
            backdrop.classList.add("is-visible");
            document.body.classList.add("is-sidebar-open");
        }

        function closeSidebar() {
            sidebar.classList.remove("is-open");
            backdrop.classList.remove("is-visible");
            document.body.classList.remove("is-sidebar-open");
        }

        toggle.addEventListener("click", () => {
            if (sidebar.classList.contains("is-open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        backdrop.addEventListener("click", closeSidebar);

        window.addEventListener("resize", () => {
            if (window.innerWidth > 1024) {
                closeSidebar();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", initSidebar);
})();