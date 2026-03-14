const state = {
  displayName: 'AiTrans 截图翻译',
  configured: false,
};

function setStatus(message, tone = 'info') {
  const status = document.getElementById('status');
  status.textContent = message;
  status.dataset.tone = tone;
}

function setHint(message) {
  document.getElementById('hint').textContent = message;
}

function syncForm(guide) {
  const baseUrlInput = document.getElementById('baseUrl');
  const apiKeyInput = document.getElementById('apiKey');
  const captureShortcutInput = document.getElementById('captureShortcut');
  const runtimeDraft = guide?.runtimeDraft || {};
  const desktopDraft = guide?.desktopDraft || {};

  if (document.activeElement !== baseUrlInput) {
    baseUrlInput.value = runtimeDraft.baseUrl || '';
  }
  if (document.activeElement !== apiKeyInput && !runtimeDraft.apiKeyPresent) {
    apiKeyInput.value = '';
  }
  if (document.activeElement !== captureShortcutInput) {
    captureShortcutInput.value = desktopDraft.captureShortcut || 'CommandOrControl+Shift+1';
  }
}

function render(payload) {
  const displayName = payload?.product?.displayName || state.displayName;
  const guide = payload?.guide || {};
  const configured = Boolean(guide.configured);
  const capabilities = guide.capabilities || {};

  state.displayName = displayName;
  state.configured = configured;

  document.getElementById('displayName').textContent = displayName;
  document.getElementById('configPath').textContent = guide.runtimeOverridesPath || '未检测到配置路径';
  document.getElementById('entryModeChip').textContent = `入口模式：${capabilities.entryMode || 'tray_and_shortcut'}`;
  document.getElementById('shortcutChip').textContent = `快捷键：${capabilities.shortcutAvailable === false ? '不可用' : '可用'}`;
  document.getElementById('captureChip').textContent = `截图能力：${capabilities.screenCaptureAvailable === false ? '不可用' : '可用'}`;

  syncForm(guide);

  if (capabilities.screenCaptureAvailable === false) {
    setStatus('当前无法获取屏幕内容，请先处理系统权限、远程桌面限制或显卡采集环境问题', 'error');
    setHint(capabilities.screenCaptureMessage || '截图主链已降级为引导模式；问题解决前不要继续发起截图。');
  } else if (capabilities.shortcutAvailable === false) {
    setStatus('全局快捷键暂不可用，当前已降级为仅托盘入口', 'warning');
    setHint(capabilities.shortcutMessage || '请在本窗口重新设置快捷键；在此之前仍可通过托盘入口开始截图。');
  } else if (configured) {
    setStatus('翻译端点已可用，可以直接开始截图', 'success');
    setHint('保存后立即生效，不需要重新安装。你可以直接回到托盘，拖选区域或使用整屏模式开始截图。');
  } else {
    setStatus('尚未完成翻译端点配置，请先填写并保存 base_url / api_key', 'warning');
    setHint('优先通过本窗口完成配置；只有在高级排障时才需要手动打开配置文件。');
  }
}

async function refreshGuide() {
  const guide = await window.aitransDesktop.getSetupGuideState();
  render({
    product: {
      displayName: state.displayName,
    },
    guide,
  });
}

window.aitransDesktop.onSetupData((payload) => {
  render(payload);
});

document.getElementById('setupForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  await saveConfig(false);
});

async function saveConfig(startCapture) {
  const saveButton = document.getElementById('save');
  const startButton = document.getElementById('saveAndStart');
  const baseUrl = document.getElementById('baseUrl').value.trim();
  const apiKey = document.getElementById('apiKey').value.trim();
  const captureShortcut = document.getElementById('captureShortcut').value.trim();

  saveButton.disabled = true;
  startButton.disabled = true;
  setStatus(startCapture ? '正在保存并准备截图…' : '正在保存配置…', 'info');

  try {
    const result = await window.aitransDesktop.saveSetupConfig({ baseUrl, apiKey, captureShortcut, startCapture });
    if (!result?.ok) {
      setStatus(result?.error || '保存配置失败', 'error');
      return;
    }
    render({
      product: {
        displayName: state.displayName,
      },
      guide: result.guide || {},
    });
    setStatus(startCapture ? '配置已保存，正在进入截图' : '配置已保存，可以直接开始截图翻译', 'success');
  } finally {
    saveButton.disabled = false;
    startButton.disabled = false;
  }
}

document.getElementById('saveAndStart').addEventListener('click', async () => {
  await saveConfig(true);
});

document.getElementById('openFile').addEventListener('click', async () => {
  await window.aitransDesktop.openConfigFile();
});

document.getElementById('openDir').addEventListener('click', async () => {
  await window.aitransDesktop.openConfigDirectory();
});

document.getElementById('copyPath').addEventListener('click', async () => {
  await window.aitransDesktop.copyConfigPath();
});

document.getElementById('refresh').addEventListener('click', async () => {
  await refreshGuide();
});

document.getElementById('close').addEventListener('click', async () => {
  await window.aitransDesktop.closeSetupGuide();
});

refreshGuide();
