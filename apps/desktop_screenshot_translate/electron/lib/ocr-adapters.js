const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const { resolveTesseractExecutable } = require('./provider-runtime');

const execFileAsync = promisify(execFile);
const OCR_ACCEPT_SCORE = 10;
const OCR_ACCEPT_TEXT_LENGTH = 5;

const TESSERACT_LANGUAGE_MAP = {
  auto: null,
  en: 'eng',
  zh: 'chi_sim',
  'zh-Hans': 'chi_sim',
  ja: 'jpn',
};

function detectSourceLanguageFromText(text) {
  if (typeof text !== 'string' || !text.trim()) {
    return {
      code: 'auto',
      strategy: 'empty_text_fallback',
    };
  }

  let latin = 0;
  let kana = 0;
  let han = 0;

  for (const char of text) {
    const codePoint = char.codePointAt(0) || 0;
    if ((codePoint >= 0x0041 && codePoint <= 0x007A) || (codePoint >= 0x00C0 && codePoint <= 0x024F)) {
      latin += 1;
      continue;
    }
    if (
      (codePoint >= 0x3040 && codePoint <= 0x309F)
      || (codePoint >= 0x30A0 && codePoint <= 0x30FF)
      || (codePoint >= 0x31F0 && codePoint <= 0x31FF)
    ) {
      kana += 1;
      continue;
    }
    if (
      (codePoint >= 0x3400 && codePoint <= 0x4DBF)
      || (codePoint >= 0x4E00 && codePoint <= 0x9FFF)
      || (codePoint >= 0xF900 && codePoint <= 0xFAFF)
    ) {
      han += 1;
    }
  }

  if (kana > 0) {
    return {
      code: 'ja',
      strategy: 'heuristic_post_ocr',
    };
  }
  if (han > 0) {
    return {
      code: 'zh',
      strategy: 'heuristic_post_ocr',
    };
  }
  if (latin > 0) {
    return {
      code: 'en',
      strategy: 'heuristic_post_ocr',
    };
  }
  return {
    code: 'auto',
    strategy: 'heuristic_post_ocr',
  };
}

function buildTesseractLanguages(productSpec) {
  const mapped = [];
  for (const item of productSpec.pipeline.source_languages || []) {
    const token = TESSERACT_LANGUAGE_MAP[item];
    if (token && !mapped.includes(token)) {
      mapped.push(token);
    }
  }
  if (mapped.length === 0) {
    return 'eng';
  }
  return mapped.join('+');
}

function buildTesseractLanguageProfiles(productSpec) {
  const profiles = [];
  const seen = new Set();
  const sourceLanguages = Array.isArray(productSpec?.pipeline?.source_languages)
    ? productSpec.pipeline.source_languages
    : [];

  function pushProfile(label, languages) {
    const normalized = languages.filter(Boolean);
    if (normalized.length === 0) {
      return;
    }
    const token = normalized.join('+');
    if (seen.has(token)) {
      return;
    }
    seen.add(token);
    profiles.push({
      label,
      languages: token,
    });
  }

  for (const item of sourceLanguages) {
    if (item === 'auto') {
      continue;
    }
    if (item === 'zh' || item === 'zh-Hans') {
      pushProfile('zh_en_primary', ['chi_sim', 'eng']);
      continue;
    }
    if (item === 'ja') {
      pushProfile('ja_en_fallback', ['jpn', 'eng']);
      continue;
    }
    if (item === 'en') {
      pushProfile('en_fallback', ['eng']);
    }
  }

  if (profiles.length === 0) {
    pushProfile('eng_default', ['eng']);
  }

  return profiles;
}

function buildPsmCandidates(capture) {
  const width = capture?.size?.width || 0;
  const height = capture?.size?.height || 0;
  const ratio = height > 0 ? width / height : 1;

  if (height > 0 && (height <= 96 || ratio >= 5.5)) {
    return [7, 6, 11];
  }
  if (width > 0 && height > 0 && (width <= 320 || height <= 180)) {
    return [11, 7, 6];
  }
  return [6, 4, 11];
}

function scoreRecognizedText(text) {
  if (typeof text !== 'string') {
    return -Infinity;
  }
  const normalized = text.trim();
  if (!normalized) {
    return -Infinity;
  }

  let signal = 0;
  let noise = 0;

  for (const char of normalized) {
    const codePoint = char.codePointAt(0) || 0;
    if (
      (codePoint >= 0x30 && codePoint <= 0x39)
      || (codePoint >= 0x41 && codePoint <= 0x5A)
      || (codePoint >= 0x61 && codePoint <= 0x7A)
    ) {
      signal += 1;
      continue;
    }
    if (
      (codePoint >= 0x3040 && codePoint <= 0x30FF)
      || (codePoint >= 0x31F0 && codePoint <= 0x31FF)
    ) {
      signal += 1.3;
      continue;
    }
    if (
      (codePoint >= 0x3400 && codePoint <= 0x4DBF)
      || (codePoint >= 0x4E00 && codePoint <= 0x9FFF)
      || (codePoint >= 0xF900 && codePoint <= 0xFAFF)
    ) {
      signal += 1.4;
      continue;
    }
    if (/\s/.test(char)) {
      continue;
    }
    if (/[.,:;!?'"()[\]{}\-_/\\|+=*&%@#$~`]/.test(char)) {
      noise += 0.5;
      continue;
    }
    noise += 1.2;
  }

  return signal - noise;
}

function getElectronNativeImage() {
  const electron = require('electron');
  if (!electron || !electron.nativeImage || typeof electron.nativeImage.createFromBuffer !== 'function') {
    throw new Error('nativeImage is unavailable in current process');
  }
  return electron.nativeImage;
}

function clampByte(value) {
  return Math.max(0, Math.min(255, Math.round(value)));
}

function buildBitmapVariantPng(image, mode) {
  const nativeImage = getElectronNativeImage();
  const size = image.getSize();
  const bitmap = image.toBitmap();
  const nextBuffer = Buffer.allocUnsafe(bitmap.length);
  const grayValues = new Uint8Array(size.width * size.height);
  let sum = 0;

  for (let index = 0, pixel = 0; index < bitmap.length; index += 4, pixel += 1) {
    const blue = bitmap[index];
    const green = bitmap[index + 1];
    const red = bitmap[index + 2];
    const alpha = bitmap[index + 3];
    const grayscale = clampByte(((0.299 * red) + (0.587 * green) + (0.114 * blue) - 128) * 1.28 + 128);
    grayValues[pixel] = grayscale;
    sum += grayscale;
    nextBuffer[index + 3] = alpha;
  }

  const threshold = clampByte(Math.max(110, Math.min(188, sum / grayValues.length)));

  for (let index = 0, pixel = 0; index < bitmap.length; index += 4, pixel += 1) {
    const grayscale = grayValues[pixel];
    const value = mode === 'threshold'
      ? (grayscale >= threshold ? 255 : 0)
      : grayscale;
    nextBuffer[index] = value;
    nextBuffer[index + 1] = value;
    nextBuffer[index + 2] = value;
  }

  return nativeImage.createFromBitmap(nextBuffer, {
    width: size.width,
    height: size.height,
    scaleFactor: 1,
  }).toPNG();
}

function buildCaptureVariants(capture) {
  const variants = [
    {
      name: 'original',
      pngBuffer: capture.pngBuffer,
      stages: ['original'],
    },
  ];

  try {
    const nativeImage = getElectronNativeImage();
    const baseImage = nativeImage.createFromBuffer(capture.pngBuffer);
    const baseSize = baseImage.getSize();
    const maxDimension = Math.max(baseSize.width || 0, baseSize.height || 0);
    const upscaleFactor = maxDimension > 0 && maxDimension < 1600 ? 2 : 1;

    const preparedImage = upscaleFactor > 1
      ? baseImage.resize({
          width: Math.max(1, baseSize.width * upscaleFactor),
          height: Math.max(1, baseSize.height * upscaleFactor),
          quality: 'best',
        })
      : baseImage;

    variants.push({
      name: 'upscaled_grayscale',
      pngBuffer: buildBitmapVariantPng(preparedImage, 'grayscale'),
      stages: upscaleFactor > 1 ? ['scale2x', 'grayscale'] : ['grayscale'],
    });
    variants.push({
      name: 'upscaled_threshold',
      pngBuffer: buildBitmapVariantPng(preparedImage, 'threshold'),
      stages: upscaleFactor > 1 ? ['scale2x', 'threshold'] : ['threshold'],
    });
  } catch {
    return variants;
  }

  const width = capture?.size?.width || 0;
  const height = capture?.size?.height || 0;
  const ratio = height > 0 ? width / height : 1;
  if (height > 0 && (height <= 96 || ratio >= 5.5)) {
    return [variants[1], variants[2], variants[0]].filter(Boolean);
  }
  return variants.filter(Boolean);
}

function buildRecognitionAttempts(capture, productSpec) {
  const languageProfiles = buildTesseractLanguageProfiles(productSpec);
  const psmCandidates = buildPsmCandidates(capture);
  const variants = buildCaptureVariants(capture);
  const attempts = [];
  const priorities = [
    [0, 0, 0],
    [0, 1, 0],
    [0, 1, 1],
    [0, 2, 0],
    [1, 1, 0],
    [1, 2, 1],
  ];

  for (const [languageIndex, variantIndex, psmIndex] of priorities) {
    const languageProfile = languageProfiles[languageIndex];
    const variant = variants[variantIndex];
    const psm = psmCandidates[psmIndex];
    if (!languageProfile || !variant || typeof psm !== 'number') {
      continue;
    }
    attempts.push({
      languageProfile,
      variant,
      psm,
    });
  }

  return attempts;
}

async function withTemporaryWorkspace(callback) {
  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'aitrans-ocr-'));
  try {
    return await callback(tmpRoot);
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  }
}

async function recognizeWithTesseract(imagePath, attempt, implementationConfig) {
  const { executable, source, tessdataDir } = resolveTesseractExecutable(implementationConfig);
  const args = [
    imagePath,
    'stdout',
    '-l',
    attempt.languageProfile.languages,
    '--oem',
    '1',
    '--psm',
    String(attempt.psm),
    '-c',
    'preserve_interword_spaces=1',
  ];
  if (tessdataDir) {
    args.push('--tessdata-dir', tessdataDir);
  }
  const result = await execFileAsync(executable, args, {
    windowsHide: true,
    maxBuffer: 16 * 1024 * 1024,
  });
  const text = (result.stdout || '').trim();
  if (!text) {
    const stderr = (result.stderr || '').trim();
    throw new Error(stderr || 'tesseract returned empty OCR text');
  }
  const sourceLanguage = detectSourceLanguageFromText(text);
  return {
    provider: 'tesseract',
    text,
    sourceLanguage: sourceLanguage.code,
    diagnostics: {
      languages: attempt.languageProfile.languages,
      languageProfile: attempt.languageProfile.label,
      psm: attempt.psm,
      imageVariant: attempt.variant.name,
      preprocessStages: attempt.variant.stages,
      executable,
      executableSource: source,
      tessdataDir,
      stderr: (result.stderr || '').trim(),
      sourceLanguageDetection: sourceLanguage.strategy,
      textScore: scoreRecognizedText(text),
    },
  };
}

async function recognizeWithWindowsOcr() {
  throw new Error(
    'windows_ocr_api requires packaged Windows app identity; unpackaged Electron MVP should fall back to tesseract first',
  );
}

async function recognizeText(capture, productSpec, implementationConfig) {
  const failures = [];
  return withTemporaryWorkspace(async (tmpRoot) => {
    for (const provider of implementationConfig.providers.ocr_chain) {
      try {
        if (provider === 'windows_ocr_api') {
          return await recognizeWithWindowsOcr();
        }
        if (provider === 'tesseract') {
          const attempts = buildRecognitionAttempts(capture, productSpec);
          const successes = [];

          for (const [index, attempt] of attempts.entries()) {
            const imagePath = path.join(tmpRoot, `capture-${index + 1}-${attempt.variant.name}.png`);
            await fs.writeFile(imagePath, attempt.variant.pngBuffer);
            try {
              const result = await recognizeWithTesseract(imagePath, attempt, implementationConfig);
              successes.push(result);
              const currentScore = result.diagnostics?.textScore ?? -Infinity;
              if (currentScore >= OCR_ACCEPT_SCORE && result.text.trim().length >= OCR_ACCEPT_TEXT_LENGTH) {
                return result;
              }
            } catch (error) {
              const message = error instanceof Error ? error.message : String(error);
              failures.push(
                `${provider}[${attempt.languageProfile.label}|${attempt.variant.name}|psm=${attempt.psm}]: ${message}`,
              );
            }
          }

          if (successes.length > 0) {
            successes.sort((left, right) => {
              const rightScore = right.diagnostics?.textScore ?? -Infinity;
              const leftScore = left.diagnostics?.textScore ?? -Infinity;
              return rightScore - leftScore;
            });
            return successes[0];
          }
          continue;
        }
        failures.push(`${provider}: unsupported provider`);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        failures.push(`${provider}: ${message}`);
      }
    }
    throw new Error(`no OCR provider succeeded: ${failures.join(' | ')}`);
  });
}

module.exports = {
  buildTesseractLanguages,
  recognizeText,
};
