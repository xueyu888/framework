(function () {
  const vscode = acquireVsCodeApi();
  const markdownIt = typeof window.markdownit === "function"
    ? window.markdownit({
      html: false,
      linkify: true,
      typographer: true,
      breaks: false,
    })
    : null;

  const state = {
    text: "",
    version: -1,
    blocks: [],
    activeIndex: -1,
    rawOpen: false,
    hasDocument: false,
  };

  const blockList = document.getElementById("blockList");
  const emptyState = document.getElementById("emptyState");
  const rawPane = document.getElementById("rawPane");
  const rawTextarea = document.getElementById("rawTextarea");
  const applyRawBtn = document.getElementById("applyRawBtn");
  const rawBtn = document.getElementById("rawBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const editorShell = document.querySelector(".editor-shell");

  window.addEventListener("message", (event) => {
    const message = event.data;
    if (!message || message.type !== "document") {
      return;
    }
    state.hasDocument = true;
    state.text = typeof message.text === "string" ? message.text : "";
    state.version = Number.isFinite(message.version) ? message.version : state.version;
    state.blocks = parseMarkdownBlocks(state.text);
    rawTextarea.value = state.text;
    render();
  });

  rawBtn.addEventListener("click", () => {
    state.rawOpen = !state.rawOpen;
    renderShellState();
  });

  applyRawBtn.addEventListener("click", () => {
    commitWholeDocument(rawTextarea.value);
  });

  refreshBtn.addEventListener("click", () => {
    requestDocumentSync();
  });

  render();
  requestDocumentSync();

  function renderShellState() {
    editorShell.classList.toggle("raw-open", state.rawOpen);
    rawPane.hidden = !state.rawOpen;
    rawBtn.textContent = state.rawOpen ? "Hide Raw" : "Show Raw";
  }

  function render() {
    renderShellState();
    blockList.innerHTML = "";
    emptyState.hidden = !shouldShowEmptyState();
    emptyState.textContent = getEmptyStateText();

    state.blocks.forEach((block, index) => {
      const blockEl = document.createElement("section");
      blockEl.className = "block";
      if (state.activeIndex === index) {
        blockEl.classList.add("active");
      }

      const actions = document.createElement("div");
      actions.className = "block-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "block-action-btn";
      editBtn.textContent = state.activeIndex === index ? "Done" : "Edit";
      editBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        if (state.activeIndex === index) {
          const textarea = blockEl.querySelector(".block-editor");
          commitBlock(index, textarea.value);
          state.activeIndex = -1;
        } else {
          state.activeIndex = index;
        }
        render();
      });
      actions.appendChild(editBtn);

      const insertBtn = document.createElement("button");
      insertBtn.type = "button";
      insertBtn.className = "block-action-btn";
      insertBtn.textContent = "+";
      insertBtn.title = "Insert paragraph below";
      insertBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        insertBlock(index + 1, "");
      });
      actions.appendChild(insertBtn);

      const preview = document.createElement("div");
      preview.className = "block-preview";
      preview.innerHTML = renderBlock(block);
      preview.addEventListener("click", () => {
        state.activeIndex = index;
        render();
      });

      const textarea = document.createElement("textarea");
      textarea.className = "block-editor";
      textarea.value = block.raw;
      textarea.spellcheck = false;
      textarea.addEventListener("keydown", (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault();
          commitBlock(index, textarea.value);
          state.activeIndex = -1;
          render();
          return;
        }
        if (event.key === "Escape") {
          event.preventDefault();
          state.activeIndex = -1;
          render();
        }
      });
      textarea.addEventListener("blur", () => {
        if (state.activeIndex !== index) {
          return;
        }
        commitBlock(index, textarea.value);
        state.activeIndex = -1;
        render();
      });

      blockEl.appendChild(actions);
      blockEl.appendChild(preview);
      blockEl.appendChild(textarea);
      blockList.appendChild(blockEl);

      if (state.activeIndex === index) {
        requestAnimationFrame(() => {
          textarea.focus();
          textarea.selectionStart = textarea.value.length;
          textarea.selectionEnd = textarea.value.length;
        });
      }
    });

    const spacer = document.createElement("div");
    spacer.className = "block-spacer";
    blockList.appendChild(spacer);
  }

  function shouldShowEmptyState() {
    if (!state.hasDocument) {
      return true;
    }
    return state.blocks.length === 0;
  }

  function getEmptyStateText() {
    if (!state.hasDocument) {
      return "Loading Markdown document...";
    }
    if (state.text.trim().length === 0) {
      return "Markdown document is empty.";
    }
    return "No renderable blocks detected.";
  }

  function requestDocumentSync() {
    vscode.postMessage({ type: "ready" });
  }

  let readyRetries = 0;
  const readyRetryTimer = window.setInterval(() => {
    if (state.hasDocument || readyRetries >= 8) {
      window.clearInterval(readyRetryTimer);
      return;
    }
    readyRetries += 1;
    requestDocumentSync();
  }, 300);

  function renderBlock(block) {
    if (!markdownIt) {
      return `<pre>${escapeHtml(block.raw)}</pre>`;
    }
    const source = block.raw.trim().length ? block.raw : "\n";
    const html = markdownIt.render(source);
    const host = document.createElement("div");
    host.innerHTML = html;

    if (window.renderMathInElement) {
      window.renderMathInElement(host, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true },
        ],
        throwOnError: false,
      });
    }
    return host.innerHTML || "&nbsp;";
  }

  function commitBlock(index, raw) {
    const nextBlocks = state.blocks.slice();
    nextBlocks[index] = {
      ...nextBlocks[index],
      raw,
    };
    commitBlocks(nextBlocks);
  }

  function insertBlock(index, raw) {
    const nextBlocks = state.blocks.slice();
    nextBlocks.splice(index, 0, {
      id: `block-${Date.now()}-${index}`,
      type: "paragraph",
      raw,
    });
    commitBlocks(nextBlocks);
    state.activeIndex = index;
    render();
  }

  function commitBlocks(blocks) {
    const nextText = blocks
      .map((block) => block.raw.replace(/\s+$/g, ""))
      .join("\n\n")
      .replace(/\n{3,}/g, "\n\n");
    commitWholeDocument(nextText);
  }

  function commitWholeDocument(nextText) {
    state.text = nextText;
    rawTextarea.value = nextText;
    vscode.postMessage({
      type: "edit",
      text: nextText,
    });
  }

  function parseMarkdownBlocks(text) {
    const normalized = String(text || "").replace(/\r\n/g, "\n");
    if (!normalized.trim()) {
      return [];
    }
    const lines = normalized.split("\n");
    const blocks = [];
    let index = 0;
    let blockId = 0;

    while (index < lines.length) {
      const line = lines[index];

      if (!line.trim()) {
        index += 1;
        continue;
      }

      if (/^(```|~~~)/.test(line)) {
        const fence = line.slice(0, 3);
        const bucket = [line];
        index += 1;
        while (index < lines.length) {
          bucket.push(lines[index]);
          if (lines[index].startsWith(fence)) {
            index += 1;
            break;
          }
          index += 1;
        }
        blocks.push(makeBlock(blockId++, "code", bucket.join("\n")));
        continue;
      }

      if (line.trim() === "$$") {
        const bucket = [line];
        index += 1;
        while (index < lines.length) {
          bucket.push(lines[index]);
          if (lines[index].trim() === "$$") {
            index += 1;
            break;
          }
          index += 1;
        }
        blocks.push(makeBlock(blockId++, "math", bucket.join("\n")));
        continue;
      }

      if (/^#{1,6}\s+/.test(line)) {
        blocks.push(makeBlock(blockId++, "heading", line));
        index += 1;
        continue;
      }

      if (isTableStart(lines, index)) {
        const bucket = [lines[index], lines[index + 1]];
        index += 2;
        while (index < lines.length && /\|/.test(lines[index]) && lines[index].trim()) {
          bucket.push(lines[index]);
          index += 1;
        }
        blocks.push(makeBlock(blockId++, "table", bucket.join("\n")));
        continue;
      }

      if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {
        const bucket = [line];
        index += 1;
        while (index < lines.length && /^\s*([-*+]|\d+\.)\s+/.test(lines[index])) {
          bucket.push(lines[index]);
          index += 1;
        }
        blocks.push(makeBlock(blockId++, "list", bucket.join("\n")));
        continue;
      }

      const bucket = [line];
      index += 1;
      while (index < lines.length) {
        if (!lines[index].trim()) {
          break;
        }
        if (
          /^#{1,6}\s+/.test(lines[index]) ||
          /^(```|~~~)/.test(lines[index]) ||
          lines[index].trim() === "$$" ||
          /^\s*([-*+]|\d+\.)\s+/.test(lines[index]) ||
          isTableStart(lines, index)
        ) {
          break;
        }
        bucket.push(lines[index]);
        index += 1;
      }
      blocks.push(makeBlock(blockId++, "paragraph", bucket.join("\n")));
    }
    return blocks;
  }

  function isTableStart(lines, index) {
    if (index + 1 >= lines.length) {
      return false;
    }
    if (!/\|/.test(lines[index])) {
      return false;
    }
    return /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(lines[index + 1]);
  }

  function makeBlock(id, type, raw) {
    return {
      id: `block-${id}`,
      type,
      raw,
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
