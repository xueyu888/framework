const vscode = require("vscode");

const VIEW_TYPE = "shelfMdLive.editor";

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const provider = new MarkdownLiveEditorProvider(context);
  context.subscriptions.push(
    vscode.window.registerCustomEditorProvider(VIEW_TYPE, provider, {
      webviewOptions: {
        retainContextWhenHidden: true,
      },
      supportsMultipleEditorsPerDocument: false,
    }),
    vscode.commands.registerCommand("shelfMdLive.reopenActiveAsLiveEditor", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage("No active text editor.");
        return;
      }
      await vscode.commands.executeCommand("vscode.openWith", editor.document.uri, VIEW_TYPE);
    }),
  );
}

class MarkdownLiveEditorProvider {
  /**
   * @param {vscode.ExtensionContext} context
   */
  constructor(context) {
    this.context = context;
  }

  /**
   * @param {vscode.TextDocument} document
   * @param {vscode.WebviewPanel} webviewPanel
   * @returns {Promise<void>}
   */
  async resolveCustomTextEditor(document, webviewPanel) {
    webviewPanel.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this.context.extensionUri, "webview"),
        vscode.Uri.joinPath(this.context.extensionUri, "node_modules"),
      ],
    };

    webviewPanel.webview.html = this.getHtml(webviewPanel.webview);

    const updateWebview = () => {
      webviewPanel.webview.postMessage({
        type: "document",
        text: document.getText(),
        version: document.version,
        languageId: document.languageId,
      });
    };

    const scheduleInitialSync = () => {
      const delays = [0, 120, 400];
      for (const delay of delays) {
        setTimeout(() => {
          void updateWebview();
        }, delay);
      }
    };

    const changeSubscription = vscode.workspace.onDidChangeTextDocument((event) => {
      if (event.document.uri.toString() === document.uri.toString()) {
        updateWebview();
      }
    });

    const messageSubscription = webviewPanel.webview.onDidReceiveMessage(async (message) => {
      if (!message || typeof message !== "object") {
        return;
      }
      if (message.type === "ready") {
        updateWebview();
        return;
      }
      if (message.type === "edit" && typeof message.text === "string") {
        await this.replaceDocument(document, message.text);
        return;
      }
      if (message.type === "showInfo" && typeof message.text === "string") {
        vscode.window.showInformationMessage(message.text);
      }
    });

    webviewPanel.onDidDispose(() => {
      changeSubscription.dispose();
      messageSubscription.dispose();
    });

    scheduleInitialSync();
  }

  /**
   * @param {vscode.TextDocument} document
   * @param {string} nextText
   * @returns {Thenable<boolean>}
   */
  replaceDocument(document, nextText) {
    const edit = new vscode.WorkspaceEdit();
    const fullRange = new vscode.Range(
      document.positionAt(0),
      document.positionAt(document.getText().length),
    );
    edit.replace(document.uri, fullRange, nextText);
    return vscode.workspace.applyEdit(edit);
  }

  /**
   * @param {vscode.Webview} webview
   * @returns {string}
   */
  getHtml(webview) {
    const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, "webview", "editor.css"));
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, "webview", "editor.js"));
    const markdownItUri = webview.asWebviewUri(vscode.Uri.joinPath(
      this.context.extensionUri,
      "node_modules",
      "markdown-it",
      "dist",
      "markdown-it.min.js",
    ));
    const katexJsUri = webview.asWebviewUri(vscode.Uri.joinPath(
      this.context.extensionUri,
      "node_modules",
      "katex",
      "dist",
      "katex.min.js",
    ));
    const katexCssUri = webview.asWebviewUri(vscode.Uri.joinPath(
      this.context.extensionUri,
      "node_modules",
      "katex",
      "dist",
      "katex.min.css",
    ));
    const katexAutoRenderUri = webview.asWebviewUri(vscode.Uri.joinPath(
      this.context.extensionUri,
      "node_modules",
      "katex",
      "dist",
      "contrib",
      "auto-render.min.js",
    ));
    const nonce = createNonce();

    return `<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'none'; img-src ${webview.cspSource} data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';"
    />
    <link rel="stylesheet" href="${styleUri}" />
    <link rel="stylesheet" href="${katexCssUri}" />
    <title>Shelf Markdown Live</title>
  </head>
  <body>
    <div class="app-shell">
      <header class="topbar">
        <div class="topbar-left">
          <strong>Shelf Markdown Live</strong>
          <span class="chip">Prototype</span>
        </div>
        <div class="topbar-right">
          <button id="refreshBtn" class="ghost-btn" type="button">Refresh</button>
          <button id="rawBtn" class="ghost-btn" type="button">Show Raw</button>
        </div>
      </header>

      <main class="editor-shell">
        <aside id="rawPane" class="raw-pane" hidden>
          <textarea id="rawTextarea" spellcheck="false"></textarea>
          <div class="raw-actions">
            <button id="applyRawBtn" class="primary-btn" type="button">Apply Raw</button>
          </div>
        </aside>

        <section class="doc-shell">
          <div id="emptyState" class="empty-state" hidden>Open a Markdown document to start.</div>
          <div id="blockList" class="block-list"></div>
        </section>
      </main>
    </div>

    <script nonce="${nonce}" src="${markdownItUri}"></script>
    <script nonce="${nonce}" src="${katexJsUri}"></script>
    <script nonce="${nonce}" src="${katexAutoRenderUri}"></script>
    <script nonce="${nonce}" src="${scriptUri}"></script>
  </body>
</html>`;
  }
}

function createNonce() {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let value = "";
  for (let index = 0; index < 32; index += 1) {
    value += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return value;
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
