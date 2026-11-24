/**
 * Проверка ссылок и ассетов статической сборки (docs/).
 *
 * Проверяет:
 *   - все локальные href/src в docs/index.html и docs/presentation/index.html;
 *   - url(...) внутри CSS;
 *   - наличие ключевых файлов сборки (app.html, 404.html, .nojekyll, архив, PDF).
 *
 * Внешние ссылки (http/https) не запрашиваются: сеть в CI может быть недоступна.
 *
 * Запуск: npm run check:links  (после npm run build:static)
 */
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DOCS = path.join(ROOT, 'docs');
const errors = [];
let checked = 0;

function exists(relativePath) {
  return fs.existsSync(path.join(DOCS, relativePath));
}

function isExternal(url) {
  return /^(https?:|mailto:|tel:|data:|javascript:|#)/.test(url);
}

function checkLocal(url, fromFile) {
  if (!url || isExternal(url)) return;
  const clean = url.split('#')[0].split('?')[0];
  if (!clean) return;
  checked += 1;
  const target = clean.startsWith('/')
    ? path.join(DOCS, clean)
    : path.resolve(path.dirname(path.join(DOCS, fromFile)), clean);
  if (!fs.existsSync(target)) {
    errors.push(`${fromFile}: ${url}`);
  }
}

function checkHtml(relativeFile) {
  const html = fs.readFileSync(path.join(DOCS, relativeFile), 'utf8');
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    checkLocal(match[1], relativeFile);
  }
}

function checkCss(relativeFile) {
  const css = fs.readFileSync(path.join(DOCS, relativeFile), 'utf8');
  for (const match of matchAll(css, /url\('([^']+)'\)/g)) {
    if (isExternal(match)) continue;
    checked += 1;
    const target = path.resolve(path.dirname(path.join(DOCS, relativeFile)), match);
    if (!fs.existsSync(target)) errors.push(`${relativeFile}: url(${match})`);
  }
}

function matchAll(text, regex) {
  return [...text.matchAll(regex)].map((m) => m[1]);
}

// --- обязательные файлы сборки ------------------------------------------------
const required = [
  'index.html',
  'app.html',
  '404.html',
  '.nojekyll',
  'downloads/podrabotka-msk-android-preview.zip',
  'presentation/index.html',
  'presentation/podrabotka-msk-deck.pdf',
  'screenshots/og-cover.png',
  'styles/demo.css',
];
for (const file of required) {
  if (!exists(file)) errors.push(`нет файла сборки: docs/${file}`);
}

// --- ссылки ------------------------------------------------------------------
if (exists('index.html')) checkHtml('index.html');
if (exists('presentation/index.html')) checkHtml('presentation/index.html');
if (exists('styles/demo.css')) checkCss('styles/demo.css');

// --- архив содержит оба HTML -------------------------------------------------
const zipPath = path.join(DOCS, 'downloads', 'podrabotka-msk-android-preview.zip');
if (fs.existsSync(zipPath)) {
  const raw = fs.readFileSync(zipPath).toString('latin1');
  for (const entry of ['index.html', 'demo.html', '.txt']) {
    if (!raw.includes(entry)) errors.push(`в архиве нет ${entry}`);
  }
}

if (errors.length) {
  console.error(`Проверка ссылок: ${errors.length} ошибок (проверено ${checked})`);
  for (const error of errors) console.error(`  ✗ ${error}`);
  process.exit(1);
}

console.log(`Проверка ссылок: ок (${checked} локальных ссылок и ассетов)`);
