#!/usr/bin/env node
/*
 * My HERO 背景ハーネス（CLAUDE.md §1-7 の描画コール予算チェック）
 *   使い方: node tools/render_bg.js [path/to/html]   （省略時 game/my_hero.html）
 *
 * やること:
 *   1. bgDraw() の switch から現役の背景関数を自動列挙
 *   2. 各関数を cam/fr を変えて4条件で実行し、
 *      - 描画コール数（fill/stroke/fillRect/beginPath等）を計測
 *      - 引数の NaN / Infinity を検出（iOS Safari の addColorStop は NaN で無言クラッシュする）
 *   3. 予算超過（bgGrass の実測値を上限とする）を FAIL 判定
 *   4. `canvas` パッケージがあれば tools/out/ に PNG を描き出す（無くても 1〜3 は動く）
 *
 * 終了コード: 0=OK / 1=予算超過 or NaN検出 or 実行時エラー
 */
'use strict';
const fs = require('fs');
const path = require('path');

const file = process.argv[2] || path.join(__dirname, '..', 'game', 'my_hero.html');
const html = fs.readFileSync(file, 'utf8');

// ---- 対象関数の抽出 ----
function grabFn(name) {
  const i = html.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('function not found: ' + name);
  let d = 0, j = html.indexOf('{', i);
  for (; j < html.length; j++) {
    if (html[j] === '{') d++;
    else if (html[j] === '}') { d--; if (d === 0) break; }
  }
  return html.slice(i, j + 1);
}

// bgDraw の switch から現役の bg 関数を列挙
const sw = grabFn('bgDraw');
const active = [...new Set([...sw.matchAll(/case\s+\d+:\s*(bg\w+)\(\)/g)].map(m => m[1]))];
if (active.length === 0) { console.error('bgDraw から背景関数を検出できない'); process.exit(1); }

// 予算基準: bgGrass（既存最重量）。存在しなければ 256 固定
const BASELINE_FN = 'bgGrass';

// ---- モック ctx（コール計測 + NaN検出）----
function makeMock(counter, nanLog, fnName) {
  const numCheck = (args, api) => {
    for (const a of args) {
      if (typeof a === 'number' && !isFinite(a)) {
        nanLog.push(fnName + ': ' + api + '(' + args.map(x => String(x).slice(0, 8)).join(',') + ')');
        return;
      }
    }
  };
  const grad = () => ({ addColorStop(off, col) {
    if (typeof col === 'string' && col.indexOf('NaN') >= 0) nanLog.push(fnName + ': addColorStop 色に NaN: ' + col);
    if (typeof off === 'number' && !isFinite(off)) nanLog.push(fnName + ': addColorStop offset NaN');
  }});
  const draw = (api) => function (...a) { counter.n++; numCheck(a, api); };
  const geom = (api) => function (...a) { numCheck(a, api); };
  return {
    fillStyle: '', strokeStyle: '', globalAlpha: 1, lineWidth: 1, lineCap: '', lineJoin: '',
    fillRect: draw('fillRect'), strokeRect: draw('strokeRect'),
    fill: draw('fill'), stroke: draw('stroke'), beginPath: draw('beginPath'), clip: draw('clip'),
    drawImage: draw('drawImage'), fillText: draw('fillText'), strokeText: draw('strokeText'),
    closePath() {}, moveTo: geom('moveTo'), lineTo: geom('lineTo'),
    arc: geom('arc'), arcTo: geom('arcTo'),
    quadraticCurveTo: geom('quadraticCurveTo'), bezierCurveTo: geom('bezierCurveTo'), rect: geom('rect'),
    save() {}, restore() {}, translate: geom('translate'), rotate: geom('rotate'),
    scale: geom('scale'), setTransform() {},
    createLinearGradient: (...a) => (numCheck(a, 'createLinearGradient'), grad()),
    createRadialGradient: (...a) => (numCheck(a, 'createRadialGradient'), grad()),
    ellipse() { nanLog.push(fnName + ': ctx.ellipse が直接呼ばれた（禁止API）'); }
  };
}

// ---- 実行 ----
// ★v293 グラデーションのキャッシュ経由になったので、ヘルパーも取り込む
const helpers = ['ctxEllipse', '_gcOf', 'gradL', 'gradR', 'fillSky'];
const srcAll = [...helpers, BASELINE_FN, ...active.filter(n => n !== BASELINE_FN)]
  .filter((v, i, a) => a.indexOf(v) === i)
  .map(grabFn).join('\n');

const PRELUDE = 'var GRAD_CACHE_MAX=240,SKY_CACHE_MAX=2,CV_K=1.25,_skyCv=[];'
  // fillSky はオフスクリーンcanvasを使うので、Node側では空グラデの塗り1回として数える
  + 'var document={createElement:function(){return {getContext:function(){return ctx;},width:0,height:0};}};';
const CONDS = [[0, 0], [37, 271], [240, 2400], [601, 6013]]; // [fr, cam]
const W = 390, Hh = 390, GROUND = 335;
let fail = 0;
const results = [];

for (const name of [BASELINE_FN, ...active.filter(n => n !== BASELINE_FN)]) {
  let mx = 0, tot = 0;
  const nanLog = [];
  let err = null;
  for (const [fr, cam] of CONDS) {
    const counter = { n: 0 };
    try {
      new Function('ctx', 'W', 'H', 'GROUND', 'cam', 'fr', PRELUDE + '\n' + srcAll + '\n' + name + '();')(
        makeMock(counter, nanLog, name), W, Hh, GROUND, cam, fr);
    } catch (e) { err = e.message; break; }
    tot += counter.n; if (counter.n > mx) mx = counter.n;
  }
  results.push({ name, avg: Math.round(tot / CONDS.length), max: mx, nanLog, err });
}

const budget = (results.find(r => r.name === BASELINE_FN) || { max: 256 }).max || 256;
console.log('== My HERO 背景ハーネス ==');
console.log('file   : ' + file);
console.log('budget : ' + budget + ' コール/frame（' + BASELINE_FN + ' 実測）\n');
console.log('関数           平均   最大   判定');
for (const r of results) {
  let verdict = 'OK';
  if (r.err) { verdict = 'ERROR ' + r.err; fail++; }
  else if (r.nanLog.length) { verdict = 'NaN検出'; fail++; }
  else if (r.max > budget) { verdict = '予算超過'; fail++; }
  console.log(
    r.name.padEnd(13) + String(r.avg).padStart(5) + String(r.max).padStart(7) + '   ' + verdict);
  for (const l of r.nanLog.slice(0, 5)) console.log('    ! ' + l);
}

// ---- 任意: PNG 描き出し ----
let rendered = false;
try {
  const { createCanvas } = require('canvas');
  const outDir = path.join(__dirname, 'out');
  fs.mkdirSync(outDir, { recursive: true });
  for (const name of active) {
    const cv = createCanvas(W * CONDS.length + 6 * (CONDS.length + 1), Hh + 10);
    const c = cv.getContext('2d');
    c.fillStyle = '#101014'; c.fillRect(0, 0, cv.width, cv.height);
    CONDS.forEach(([fr, cam], k) => {
      const s = createCanvas(W, Hh);
      new Function('ctx', 'W', 'H', 'GROUND', 'cam', 'fr', PRELUDE + '\n' + srcAll + '\n' + name + '();')(
        s.getContext('2d'), W, Hh, GROUND, cam, fr);
      c.drawImage(s, 6 + k * (W + 6), 5);
    });
    fs.writeFileSync(path.join(outDir, name + '.png'), cv.toBuffer('image/png'));
  }
  rendered = true;
  console.log('\nPNG: tools/out/ に ' + active.length + ' 本（各4条件）を描き出した。目視確認すること。');
} catch (e) {
  console.log('\n（canvas パッケージ未導入のため PNG 描き出しはスキップ。コール計測とNaN検出は完了）');
}

console.log(fail === 0 ? '\n\u2705 背景ゲート通過' : '\n\u274c ' + fail + ' 件の問題 — 修正してから再実行');
process.exit(fail === 0 ? 0 : 1);
