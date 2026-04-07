(function () {
    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function initAssignmentsPage() {
        const config = document.getElementById("assignment-page-config");
        const backdrop = document.querySelector("[data-assignment-backdrop]");
        const panel = document.querySelector("[data-assignment-panel]");
        const panelBody = document.querySelector("[data-assignment-panel-body]");
        const panelSubheading = document.querySelector("[data-assignment-panel-subheading]");
        const openButtons = document.querySelectorAll("[data-assignment-open]");
        const closeButtons = document.querySelectorAll("[data-assignment-close]");

        if (!config || !backdrop || !panel || !panelBody || !panelSubheading) {
            return;
        }

        const csrfToken = config.dataset.csrfToken;
        const assignUrlTemplate = config.dataset.assignUrlTemplate;
        const unassignUrlTemplate = config.dataset.unassignUrlTemplate;

        function openPanel() {
            backdrop.classList.add("is-open");
            panel.classList.add("is-open");
            document.body.classList.add("is-assignment-panel-open");
        }

        function closePanel() {
            backdrop.classList.remove("is-open");
            panel.classList.remove("is-open");
            document.body.classList.remove("is-assignment-panel-open");
        }

        function renderPanel(data) {
            panelSubheading.textContent = `${data.date} · ${data.duty_name}`;

            const assignedHtml = data.assigned.length
                ? data.assigned.map((item) => `
                    <div class="assignment-panel__person assignment-panel__person--assigned">
                        <div>
                            <div class="assignment-panel__person-name">${escapeHtml(item.name)}</div>
                            <div class="assignment-panel__person-meta">${escapeHtml(item.rank)}${item.unit ? " · " + escapeHtml(item.unit) : ""}</div>
                        </div>
                        <form method="post" action="${unassignUrlTemplate.replace("__ASSIGNMENT_ID__", item.id)}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="button button--sm button--danger">Снять</button>
                        </form>
                    </div>
                `).join("")
                : `<div class="assignment-panel__empty">Пока никто не назначен.</div>`;

            const availableHtml = data.available.length
                ? data.available.map((item) => `
                    <div class="assignment-panel__person">
                        <div>
                            <div class="assignment-panel__person-name">${escapeHtml(item.name)}</div>
                            <div class="assignment-panel__person-meta">${escapeHtml(item.rank)}${item.unit ? " · " + escapeHtml(item.unit) : ""}</div>
                        </div>
                        <form method="post" action="${assignUrlTemplate.replace("__PLAN_ID__", data.plan_id)}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <input type="hidden" name="person_id" value="${item.id}">
                            <button type="submit" class="button button--sm button--primary">Назначить</button>
                        </form>
                    </div>
                `).join("")
                : `<div class="assignment-panel__empty">Нет доступных сотрудников.</div>`;

            panelBody.innerHTML = `
                <section class="assignment-panel__section">
                    <div class="assignment-panel__section-title">${escapeHtml(data.duty_name)}</div>
                    <div class="assignment-panel__section-meta">
                        ${escapeHtml(data.date)} · ${escapeHtml(data.unit_name)} · ${data.current_count}/${data.required_people}
                    </div>
                </section>

                <section class="assignment-panel__section">
                    <div class="assignment-panel__section-title">Назначенные сотрудники</div>
                    <div class="assignment-panel__list">
                        ${assignedHtml}
                    </div>
                </section>

                <section class="assignment-panel__section">
                    <div class="assignment-panel__section-title">Доступные сотрудники</div>
                    <div class="assignment-panel__list">
                        ${availableHtml}
                    </div>
                </section>
            `;
        }

        openButtons.forEach((button) => {
            button.addEventListener("click", async () => {
                const fetchUrl = button.dataset.fetchUrl;
                if (!fetchUrl) return;

                panelSubheading.textContent = "Загрузка...";
                panelBody.innerHTML = `<div class="assignment-panel__loading">Загрузка данных…</div>`;
                openPanel();

                try {
                    const response = await fetch(fetchUrl, {
                        headers: { "X-Requested-With": "XMLHttpRequest" }
                    });
                    const data = await response.json();

                    if (!response.ok) {
                        panelBody.innerHTML = `<div class="assignment-panel__error">${escapeHtml(data.error || "Не удалось загрузить данные.")}</div>`;
                        return;
                    }

                    renderPanel(data);
                } catch (error) {
                    panelBody.innerHTML = `<div class="assignment-panel__error">Ошибка загрузки данных.</div>`;
                }
            });
        });

        closeButtons.forEach((button) => {
            button.addEventListener("click", closePanel);
        });

        backdrop.addEventListener("click", closePanel);

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closePanel();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", initAssignmentsPage);
})();