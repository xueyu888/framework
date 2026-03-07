from __future__ import annotations

from html import escape
import json

from framework_core import Base, BoundaryDefinition, BoundaryItem, Capability, VerificationInput, VerificationResult, verify
from knowledge_base_demo.workspace import compose_workspace_flow
from project_runtime.knowledge_base import KnowledgeBaseProjectConfig, load_knowledge_base_project

KNOWLEDGE_BASE_FRONTEND_CAPABILITIES = (
    Capability("C1", "Compose search, filter, result, detail, and edit-ready compose regions into a stable knowledge workbench page"),
    Capability("C2", "Keep reading flow and create-or-edit write flow consistent inside one frontend surface"),
    Capability("C3", "Accept backend contracts without leaking backend implementation details"),
    Capability("C4", "Exclude storage, ranking, and permission engine internals"),
)

KNOWLEDGE_BASE_FRONTEND_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("VIEW", "search, filter, list, detail, and compose regions must stay explicit"),
        BoundaryItem("QUERY", "keyword, tag, status, and page parameters must stay stable"),
        BoundaryItem("DETAIL", "title, body, tags, and related articles must be readable"),
        BoundaryItem("WRITE", "create, optional draft, publish, and edit actions must expose stable feedback"),
        BoundaryItem("RESP", "loading, empty, error, and success states must remain explicit"),
        BoundaryItem("ROUTE", "workspace entry and deep-link routes must be stable"),
        BoundaryItem("A11Y", "keyboard navigation and reading order must stay intact"),
    )
)

KNOWLEDGE_BASE_FRONTEND_BASES = (
    Base("B1", "retrieval-reading layout base", "L1.M0[R1,R2]"),
    Base("B2", "write-feedback interaction base", "L1.M0[R2,R3]"),
    Base("B3", "contract handoff base", "L1.M0[R1,R3]"),
)


def _resolve_project_config(project_config: KnowledgeBaseProjectConfig | None) -> KnowledgeBaseProjectConfig:
    return project_config or load_knowledge_base_project()


def compose_knowledge_base_page(
    project_config: KnowledgeBaseProjectConfig | None = None,
    api_base_url: str | None = None,
) -> str:
    config = _resolve_project_config(project_config)
    frontend_copy = config.frontend_boundary_values
    resolved_api_base = api_base_url or config.route_boundary_values.api_prefix
    supports_draft = config.composition_profile.supports_draft
    scenario_markup = "\n".join(
        (
            f"<li><strong>{escape(scene.title)}</strong><span>{' -> '.join(escape(step) for step in scene.steps)}</span></li>"
            for scene in compose_workspace_flow(config)
        )
    )

    html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>__PAGE_TITLE__</title>
    <style>
      :root {
        --bg: #f4f1e8;
        --panel: rgba(255, 252, 245, 0.88);
        --panel-strong: #fffaf0;
        --ink: #1b1c1f;
        --muted: #6a6760;
        --accent: #0f6d62;
        --accent-soft: #d7efe9;
        --line: rgba(27, 28, 31, 0.12);
        --warn: #b2552f;
        --shadow: 0 18px 45px rgba(26, 31, 33, 0.12);
        --radius: 22px;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Source Sans 3", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(15, 109, 98, 0.12), transparent 28%),
          radial-gradient(circle at bottom right, rgba(178, 85, 47, 0.10), transparent 24%),
          linear-gradient(180deg, #fcf7ec 0%, #f3eee5 100%);
      }

      .shell {
        max-width: 1480px;
        margin: 0 auto;
        padding: 32px 20px 40px;
      }

      .hero {
        display: grid;
        grid-template-columns: 1.35fr 0.85fr;
        gap: 20px;
        margin-bottom: 20px;
      }

      .hero-card,
      .panel,
      .aside-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
      }

      .hero-card {
        padding: 28px;
        position: relative;
        overflow: hidden;
      }

      .hero-card::after {
        content: "";
        position: absolute;
        inset: auto -40px -70px auto;
        width: 180px;
        height: 180px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(15, 109, 98, 0.2), rgba(178, 85, 47, 0.08));
      }

      .hero-kicker {
        display: inline-flex;
        padding: 8px 12px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      h1 {
        margin: 18px 0 10px;
        font-size: clamp(2rem, 4vw, 3.4rem);
        line-height: 1.05;
      }

      .hero-copy {
        max-width: 760px;
        font-size: 1.02rem;
        color: var(--muted);
        line-height: 1.6;
      }

      .scene-list {
        list-style: none;
        padding: 0;
        margin: 18px 0 0;
        display: grid;
        gap: 10px;
      }

      .scene-list li {
        display: grid;
        gap: 4px;
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(27, 28, 31, 0.08);
      }

      .scene-list span {
        color: var(--muted);
        font-size: 0.94rem;
      }

      .hero-side {
        display: grid;
        gap: 20px;
      }

      .aside-card {
        padding: 20px;
      }

      .aside-card h2,
      .panel h2 {
        margin: 0 0 10px;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }

      .aside-value {
        font-size: 2.2rem;
        font-weight: 700;
      }

      .aside-meta {
        color: var(--muted);
        line-height: 1.5;
      }

      .workspace {
        display: grid;
        grid-template-columns: 0.9fr 1.4fr 1.15fr;
        gap: 20px;
        align-items: start;
      }

      .panel {
        padding: 22px;
      }

      .search-row {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
        margin-bottom: 12px;
      }

      input,
      textarea,
      select,
      button {
        font: inherit;
      }

      input,
      textarea {
        width: 100%;
        border: 1px solid rgba(27, 28, 31, 0.14);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.92);
        padding: 12px 14px;
        color: var(--ink);
      }

      textarea {
        min-height: 140px;
        resize: vertical;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 12px 16px;
        background: var(--ink);
        color: #fff;
        cursor: pointer;
        transition: transform 180ms ease, opacity 180ms ease;
      }

      button:hover { transform: translateY(-1px); }
      button:disabled { opacity: 0.56; cursor: not-allowed; }
      .ghost {
        background: transparent;
        color: var(--ink);
        border: 1px solid rgba(27, 28, 31, 0.16);
      }

      .tag-strip,
      .status-strip,
      .action-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .tag-chip,
      .status-chip {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(27, 28, 31, 0.14);
        color: var(--ink);
      }

      .tag-chip.active,
      .status-chip.active {
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
      }

      .list {
        display: grid;
        gap: 10px;
        margin-top: 16px;
      }

      .article-card {
        padding: 16px;
        border-radius: 18px;
        border: 1px solid rgba(27, 28, 31, 0.1);
        background: rgba(255, 255, 255, 0.8);
        cursor: pointer;
        transition: transform 180ms ease, border-color 180ms ease;
      }

      .article-card:hover,
      .article-card.active {
        transform: translateY(-2px);
        border-color: rgba(15, 109, 98, 0.42);
      }

      .article-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 6px;
      }

      .article-summary,
      .muted {
        color: var(--muted);
      }

      .meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
      }

      .meta-pill {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(15, 109, 98, 0.08);
        font-size: 0.82rem;
      }

      .detail-body {
        line-height: 1.7;
        white-space: pre-wrap;
      }

      .banner {
        margin-bottom: 12px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(15, 109, 98, 0.1);
        color: var(--accent);
        min-height: 48px;
      }

      .banner.error {
        background: rgba(178, 85, 47, 0.12);
        color: var(--warn);
      }

      .field {
        display: grid;
        gap: 8px;
        margin-bottom: 12px;
      }

      .field label {
        font-size: 0.92rem;
        font-weight: 600;
      }

      .panel-foot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        color: var(--muted);
      }

      @media (max-width: 1180px) {
        .hero,
        .workspace {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <article class="hero-card">
          <span class="hero-kicker">__HERO_KICKER__</span>
          <h1>__HERO_TITLE__</h1>
          <p class="hero-copy">__HERO_COPY__</p>
          <ul class="scene-list">__SCENES__</ul>
        </article>
        <div class="hero-side">
          <section class="aside-card">
            <h2>__CONTRACT_TITLE__</h2>
            <div class="aside-value">__CONTRACT_VALUE__</div>
            <p class="aside-meta">__CONTRACT_META__</p>
          </section>
          <section class="aside-card">
            <h2>__BOUNDARY_TITLE__</h2>
            <p class="aside-meta">__BOUNDARY_META__</p>
          </section>
        </div>
      </section>

      <section class="workspace">
        <section class="panel">
          <h2>__SEARCH_TITLE__</h2>
          <form id="search-form">
            <div class="search-row">
              <input id="keyword" name="keyword" type="search" placeholder="__KEYWORD_PLACEHOLDER__">
              <button type="submit">__QUERY_BUTTON_LABEL__</button>
            </div>
            <div class="field">
              <label>Status</label>
              <div class="status-strip" id="status-strip"></div>
            </div>
            <div class="field">
              <label>Tags</label>
              <div class="tag-strip" id="tag-strip"></div>
            </div>
          </form>
          <div class="panel-foot">
            <span id="list-meta">No results loaded</span>
            <button id="reset-button" class="ghost" type="button">__RESET_BUTTON_LABEL__</button>
          </div>
          <div class="list" id="article-list"></div>
        </section>

        <section class="panel">
          <div class="banner" id="detail-banner">Select an article to read.</div>
          <h2>__READ_TITLE__</h2>
          <div id="detail-view">
            <h3>__DETAIL_EMPTY_TITLE__</h3>
            <p class="muted">__DETAIL_EMPTY_DESCRIPTION__</p>
          </div>
        </section>

        <section class="panel">
          <div class="banner" id="action-banner">__ACTION_IDLE_BANNER__</div>
          <h2>__COMPOSE_TITLE__</h2>
          <form id="create-form">
            <input id="editing-slug" name="editing_slug" type="hidden">
            <div class="field">
              <label for="title">Title</label>
              <input id="title" name="title" required minlength="__TITLE_MIN__" maxlength="__TITLE_MAX__" placeholder="__TITLE_PLACEHOLDER__">
            </div>
            <div class="field">
              <label for="summary">Summary</label>
              <textarea id="summary" name="summary" required minlength="__SUMMARY_MIN__" maxlength="__SUMMARY_MAX__" placeholder="__SUMMARY_PLACEHOLDER__"></textarea>
            </div>
            <div class="field">
              <label for="body">Body</label>
              <textarea id="body" name="body" required minlength="__BODY_MIN__" maxlength="__BODY_MAX__" placeholder="__BODY_PLACEHOLDER__"></textarea>
            </div>
            <div class="field">
              <label for="tags">Tags</label>
              <input id="tags" name="tags" placeholder="__TAGS_PLACEHOLDER__">
            </div>
            <div class="action-row">
              __SAVE_DRAFT_BUTTON__
              <button type="submit" data-status="published" class="ghost">__PUBLISH_LABEL__</button>
              <button id="clear-compose" type="button" class="ghost">__CLEAR_LABEL__</button>
            </div>
          </form>
        </section>
      </section>
    </main>

    <script>
      const apiBase = __API_BASE_JSON__;
      const frontendCopy = __FRONTEND_COPY_JSON__;
      const configuredStatuses = __STATUS_OPTIONS__;
      const supportsEdit = __SUPPORTS_EDIT__;
      const supportsDraft = __SUPPORTS_DRAFT__;
      const state = {
        keyword: "",
        tag: "",
        status: "",
        selectedSlug: "",
        routeMode: "",
        submitStatus: supportsDraft ? "draft" : "published",
      };

      const articleList = document.getElementById("article-list");
      const detailView = document.getElementById("detail-view");
      const detailBanner = document.getElementById("detail-banner");
      const actionBanner = document.getElementById("action-banner");
      const tagStrip = document.getElementById("tag-strip");
      const statusStrip = document.getElementById("status-strip");
      const listMeta = document.getElementById("list-meta");
      const keywordInput = document.getElementById("keyword");
      const createForm = document.getElementById("create-form");
      const editingSlugInput = document.getElementById("editing-slug");
      const titleInput = document.getElementById("title");
      const summaryInput = document.getElementById("summary");
      const bodyInput = document.getElementById("body");
      const tagsInput = document.getElementById("tags");
      const clearComposeButton = document.getElementById("clear-compose");
      const resetButton = document.getElementById("reset-button");
      const initialParams = new URLSearchParams(window.location.search);

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      function setBanner(element, text, isError = false) {
        element.textContent = text;
        element.classList.toggle("error", isError);
      }

      function formatStatusLabel(value) {
        return value
          .split("_")
          .map((item) => item.charAt(0).toUpperCase() + item.slice(1))
          .join(" ");
      }

      function syncRoute() {
        const params = new URLSearchParams();
        if (state.keyword) params.set("keyword", state.keyword);
        if (state.tag) params.set("tag", state.tag);
        if (state.status) params.set("status", state.status);

        if (supportsEdit && state.routeMode === "edit" && editingSlugInput.value.trim()) {
          params.set("mode", "edit");
          params.set("slug", editingSlugInput.value.trim());
        } else if (state.routeMode === "create") {
          params.set("mode", "create");
        } else if (state.selectedSlug) {
          params.set("focus", "detail");
          params.set("slug", state.selectedSlug);
        }

        const nextQuery = params.toString();
        const nextUrl = nextQuery ? `${window.location.pathname}?${nextQuery}` : window.location.pathname;
        window.history.replaceState(null, "", nextUrl);
      }

      function setComposeMode(article = null) {
        if (!article) {
          editingSlugInput.value = "";
          createForm.reset();
          state.routeMode = "create";
          state.submitStatus = supportsDraft ? "draft" : "published";
          setBanner(actionBanner, supportsDraft ? "Draft state is idle." : "Compose state is idle.");
          syncRoute();
          return;
        }

        editingSlugInput.value = article.slug;
        state.selectedSlug = article.slug;
        state.routeMode = supportsEdit ? "edit" : "";
        titleInput.value = article.title;
        summaryInput.value = article.summary;
        bodyInput.value = article.body;
        tagsInput.value = article.tags.join(", ");
        state.submitStatus = article.status;
        setBanner(
          actionBanner,
          supportsEdit
            ? `Editing "${article.title}" as ${article.status}.`
            : `Loaded "${article.title}" into compose.`
        );
        syncRoute();
      }

      function renderStatusChips() {
        const options = [{ value: "", label: "All" }].concat(
          configuredStatuses.map((value) => ({ value, label: formatStatusLabel(value) }))
        );
        statusStrip.innerHTML = "";
        for (const option of options) {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "status-chip" + (state.status === option.value ? " active" : "");
          button.textContent = option.label;
          button.addEventListener("click", () => {
            state.status = option.value;
            renderStatusChips();
            loadArticles();
          });
          statusStrip.appendChild(button);
        }
      }

      async function loadTags() {
        const response = await fetch(`${apiBase}/tags`);
        if (!response.ok) {
          throw new Error("Failed to load tags.");
        }
        const payload = await response.json();
        tagStrip.innerHTML = "";

        const allButton = document.createElement("button");
        allButton.type = "button";
        allButton.className = "tag-chip" + (state.tag === "" ? " active" : "");
        allButton.textContent = "All tags";
        allButton.addEventListener("click", () => {
          state.tag = "";
          loadTags();
          loadArticles();
        });
        tagStrip.appendChild(allButton);

        for (const item of payload.items) {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "tag-chip" + (state.tag === item.name ? " active" : "");
          button.textContent = `${item.name} (${item.count})`;
          button.addEventListener("click", () => {
            state.tag = item.name;
            loadTags();
            loadArticles();
          });
          tagStrip.appendChild(button);
        }
      }

      function renderArticleCard(article) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "article-card" + (state.selectedSlug === article.slug ? " active" : "");
        button.innerHTML = `
          <div class="article-title">${escapeHtml(article.title)}</div>
          <div class="article-summary">${escapeHtml(article.summary)}</div>
          <div class="meta-row">
            ${article.tags.map((tag) => `<span class="meta-pill">${escapeHtml(tag)}</span>`).join("")}
            <span class="meta-pill">${escapeHtml(article.status)}</span>
            <span class="meta-pill">${escapeHtml(article.updated_at)}</span>
          </div>
        `;
        button.addEventListener("click", () => {
          state.selectedSlug = article.slug;
          state.routeMode = "";
          syncRoute();
          loadArticles();
          loadDetail(article.slug);
        });
        return button;
      }

      async function loadArticles() {
        const params = new URLSearchParams();
        if (state.keyword) params.set("keyword", state.keyword);
        if (state.tag) params.set("tag", state.tag);
        if (state.status) params.set("status_filter", state.status);
        setBanner(detailBanner, "Loading article list...");

        const response = await fetch(`${apiBase}/articles?${params.toString()}`);
        if (!response.ok) {
          articleList.innerHTML = "";
          detailView.innerHTML = `<h3>${escapeHtml(frontendCopy.list_error_title)}</h3><p class="muted">${escapeHtml(frontendCopy.list_error_description)}</p>`;
          listMeta.textContent = "List failed";
          setBanner(detailBanner, "Failed to load article list.", true);
          return;
        }
        const payload = await response.json();
        articleList.innerHTML = "";
        listMeta.textContent = `${payload.total} articles`;

        if (payload.items.length === 0) {
          articleList.innerHTML = `<div class="article-card"><div class="article-title">${escapeHtml(frontendCopy.list_empty_title)}</div><div class="article-summary">${escapeHtml(frontendCopy.list_empty_description)}</div></div>`;
          detailView.innerHTML = `<h3>${escapeHtml(frontendCopy.detail_no_selection_title)}</h3><p class="muted">${escapeHtml(frontendCopy.detail_no_selection_description)}</p>`;
          setBanner(detailBanner, "No result matched the current query.");
          state.selectedSlug = "";
          return;
        }

        payload.items.forEach((article) => articleList.appendChild(renderArticleCard(article)));
        const hasSelectedArticle = payload.items.some((article) => article.slug === state.selectedSlug);
        if (!hasSelectedArticle) {
          state.selectedSlug = payload.items[0].slug;
        }
        syncRoute();
        await loadDetail(state.selectedSlug);
      }

      async function loadDetail(slug) {
        if (!slug) {
          return;
        }
        setBanner(detailBanner, "Loading detail...");
        const response = await fetch(`${apiBase}/articles/${slug}`);
        if (!response.ok) {
          setBanner(detailBanner, "Failed to load detail.", true);
          return;
        }
        const article = await response.json();
        detailView.innerHTML = `
          <h3>${escapeHtml(article.title)}</h3>
          <div class="meta-row">
            ${article.tags.map((tag) => `<span class="meta-pill">${escapeHtml(tag)}</span>`).join("")}
            <span class="meta-pill">${escapeHtml(article.status)}</span>
            <span class="meta-pill">${escapeHtml(article.updated_at)}</span>
          </div>
          <p class="detail-body">${escapeHtml(article.body)}</p>
          ${supportsEdit ? `<div class="action-row"><button type="button" class="ghost" data-edit-slug="${escapeHtml(article.slug)}">${escapeHtml(frontendCopy.edit_label)}</button></div>` : ""}
          <div class="muted">Related: ${article.related_slugs.length ? article.related_slugs.map((item) => escapeHtml(item)).join(", ") : "none"}</div>
        `;
        state.selectedSlug = article.slug;
        syncRoute();
        setBanner(detailBanner, `Reading "${article.title}"`);
        const editButton = detailView.querySelector("[data-edit-slug]");
        if (editButton instanceof HTMLButtonElement) {
          editButton.addEventListener("click", () => setComposeMode(article));
        }
        if (supportsEdit && state.routeMode === "edit") {
          setComposeMode(article);
        }
      }

      createForm.addEventListener("click", (event) => {
        const target = event.target;
        if (target instanceof HTMLButtonElement && target.dataset.status) {
          state.submitStatus = target.dataset.status;
        }
      });

      createForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(createForm);
        const payload = {
          title: String(form.get("title") || ""),
          summary: String(form.get("summary") || ""),
          body: String(form.get("body") || ""),
          tags: String(form.get("tags") || "")
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          status: state.submitStatus,
        };
        const editingSlug = editingSlugInput.value.trim();
        const isUpdate = editingSlug.length > 0;

        setBanner(
          actionBanner,
          isUpdate
            ? (state.submitStatus === "published" ? "Updating published article..." : "Updating draft...")
            : (state.submitStatus === "published" ? "Publishing article..." : "Saving draft...")
        );
        const response = await fetch(
          isUpdate ? `${apiBase}/articles/${editingSlug}` : `${apiBase}/articles`,
          {
            method: isUpdate ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );
        const body = await response.json();
        if (!response.ok) {
          setBanner(actionBanner, body.detail || "Save failed.", true);
          return;
        }
        setComposeMode();
        state.selectedSlug = body.slug;
        state.routeMode = "";
        setBanner(actionBanner, `${isUpdate ? "Updated" : "Saved"} "${body.title}" as ${body.status}.`);
        await loadTags();
        await loadArticles();
      });

      document.getElementById("search-form").addEventListener("submit", (event) => {
        event.preventDefault();
        state.keyword = keywordInput.value.trim();
        loadArticles();
      });

      resetButton.addEventListener("click", () => {
        keywordInput.value = "";
        state.keyword = "";
        state.tag = "";
        state.status = "";
        state.selectedSlug = "";
        state.routeMode = "";
        setComposeMode();
        renderStatusChips();
        loadTags();
        loadArticles();
      });

      clearComposeButton.addEventListener("click", () => {
        setComposeMode();
      });

      state.keyword = initialParams.get("keyword")?.trim() || "";
      state.tag = initialParams.get("tag") || "";
      state.selectedSlug = initialParams.get("slug") || "";
      const initialStatus = initialParams.get("status");
      if (initialStatus && configuredStatuses.includes(initialStatus)) {
        state.status = initialStatus;
      }
      if (initialParams.get("mode") === "create" || (supportsEdit && initialParams.get("mode") === "edit")) {
        state.routeMode = initialParams.get("mode");
      }
      keywordInput.value = state.keyword;
      if (state.routeMode === "create") {
        setComposeMode();
      }

      renderStatusChips();
      loadTags().then(loadArticles).catch((error) => {
        console.error(error);
        setBanner(detailBanner, "Failed to bootstrap the workbench.", true);
      });
    </script>
  </body>
</html>
"""
    replacements = {
        "__API_BASE_JSON__": json.dumps(resolved_api_base, ensure_ascii=False),
        "__FRONTEND_COPY_JSON__": json.dumps(frontend_copy.to_dict(), ensure_ascii=False),
        "__STATUS_OPTIONS__": json.dumps(list(config.backend_constraint_profile.allowed_statuses), ensure_ascii=False),
        "__SUPPORTS_EDIT__": "true" if config.composition_profile.supports_edit else "false",
        "__SUPPORTS_DRAFT__": "true" if supports_draft else "false",
        "__ACTION_IDLE_BANNER__": escape(
            "Draft state is idle." if supports_draft else "Compose state is idle.",
            quote=True,
        ),
        "__SAVE_DRAFT_BUTTON__": (
            f'<button type="submit" data-status="draft">{escape(frontend_copy.save_draft_label, quote=True)}</button>'
            if supports_draft
            else ""
        ),
        "__SCENES__": scenario_markup,
        "__PAGE_TITLE__": escape(frontend_copy.page_title, quote=True),
        "__HERO_KICKER__": escape(frontend_copy.hero_kicker, quote=True),
        "__HERO_TITLE__": escape(frontend_copy.hero_title, quote=True),
        "__HERO_COPY__": escape(frontend_copy.hero_copy, quote=True),
        "__CONTRACT_TITLE__": escape(frontend_copy.contract_title, quote=True),
        "__CONTRACT_VALUE__": escape(frontend_copy.contract_value, quote=True),
        "__CONTRACT_META__": escape(frontend_copy.contract_meta, quote=True),
        "__BOUNDARY_TITLE__": escape(frontend_copy.boundary_title, quote=True),
        "__BOUNDARY_META__": escape(frontend_copy.boundary_meta, quote=True),
        "__SEARCH_TITLE__": escape(frontend_copy.search_title, quote=True),
        "__READ_TITLE__": escape(frontend_copy.read_title, quote=True),
        "__COMPOSE_TITLE__": escape(frontend_copy.compose_title, quote=True),
        "__KEYWORD_PLACEHOLDER__": escape(frontend_copy.keyword_placeholder, quote=True),
        "__QUERY_BUTTON_LABEL__": escape(frontend_copy.query_button_label, quote=True),
        "__RESET_BUTTON_LABEL__": escape(frontend_copy.reset_button_label, quote=True),
        "__DETAIL_EMPTY_TITLE__": escape(frontend_copy.detail_empty_title, quote=True),
        "__DETAIL_EMPTY_DESCRIPTION__": escape(frontend_copy.detail_empty_description, quote=True),
        "__TITLE_PLACEHOLDER__": escape(frontend_copy.title_placeholder, quote=True),
        "__SUMMARY_PLACEHOLDER__": escape(frontend_copy.summary_placeholder, quote=True),
        "__BODY_PLACEHOLDER__": escape(frontend_copy.body_placeholder, quote=True),
        "__TAGS_PLACEHOLDER__": escape(frontend_copy.tags_placeholder, quote=True),
        "__PUBLISH_LABEL__": escape(frontend_copy.publish_label, quote=True),
        "__CLEAR_LABEL__": escape(frontend_copy.clear_label, quote=True),
        "__TITLE_MIN__": str(config.backend_constraint_profile.min_title_length),
        "__TITLE_MAX__": str(config.backend_constraint_profile.max_title_length),
        "__SUMMARY_MIN__": str(config.backend_constraint_profile.min_summary_length),
        "__SUMMARY_MAX__": str(config.backend_constraint_profile.max_summary_length),
        "__BODY_MIN__": str(config.backend_constraint_profile.min_body_length),
        "__BODY_MAX__": str(config.backend_constraint_profile.max_body_length),
    }
    rendered = html
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def verify_knowledge_base_frontend(
    project_config: KnowledgeBaseProjectConfig | None = None,
) -> VerificationResult:
    config = _resolve_project_config(project_config)
    boundary_valid, boundary_errors = KNOWLEDGE_BASE_FRONTEND_BOUNDARY.validate()
    base_result = verify(
        VerificationInput(
            subject="knowledge base frontend",
            pass_criteria=[
                "page exposes search, list, detail, and compose regions",
                "detail and create-or-edit write flows share stable feedback states",
                "frontend consumes backend contract without storage assumptions",
            ],
            evidence={
                "project": config.public_summary(),
                "capabilities": [item.to_dict() for item in KNOWLEDGE_BASE_FRONTEND_CAPABILITIES],
                "boundary": KNOWLEDGE_BASE_FRONTEND_BOUNDARY.to_dict(),
                "bases": [item.to_dict() for item in KNOWLEDGE_BASE_FRONTEND_BASES],
                "workspace_scenes": [item.to_dict() for item in compose_workspace_flow(config)],
            },
        )
    )
    reasons = [*boundary_errors, *base_result.reasons]
    return VerificationResult(
        passed=boundary_valid and base_result.passed,
        reasons=reasons,
        evidence=base_result.evidence,
    )
