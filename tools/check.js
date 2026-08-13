#!/usr/bin/env node
/*
 * My HERO 出荷前ゲート（CLAUDE.md §3 の 1〜3 を機械照合）
 *   使い方: node tools/check.js game/my_hero.html
 *   終了コード: 0=全ゲート通過 / 1=違反あり（コミット禁止）
 *
 * ゲート:
 *   G1 acorn構文チェック (ecmaVersion 2020) — Node の new Function は IIFE+strict で
 *      偽エラーを出す実績があるため使わない
 *   G2 __dbg 残置 0件
 *   G3 禁止API 0件: ctx.ellipse( の呼び出し / ctx.roundRect
 *      （`ctx.ellipse?` の存在確認三項は既知の例外として除外）
 *   G4 ファイル名が半角英数字か（iOS Safari で全角名は読み込み失敗する実績）
 *   参考情報: 行数・バイト数・script ブロック数
 *
 * base64 対策: data URI の中身は事前に除去してから G2/G3 を走らせる
 * （20万字の base64 が偶然一致を量産するため）。
 */
'use strict';
const fs = require('fs');
const path = require('path');

let acorn;
try { acorn = require('acorn'); }
catch (e) {
  console.error('[SETUP] acorn が見つからない。 cd tools && npm install を先に実行すること。');
  process.exit(1);
}

const file = process.argv[2];
if (!file) { console.error('usage: node tools/check.js <path/to/html>'); process.exit(1); }
const src = fs.readFileSync(file, 'utf8');

let fail = 0;
const ok  = (m) => console.log('  \u2705 ' + m);
const bad = (m) => { console.log('  \u274c ' + m); fail++; };

console.log('== My HERO ship gates ==');
console.log('file : ' + file);
console.log('size : ' + src.split('\n').length + ' lines / ' + Buffer.byteLength(src) + ' bytes');

// ---- G4 filename ----
const base = path.basename(file);
if (/^[\x21-\x7e]+$/.test(base)) ok('G4 ファイル名は半角英数字のみ');
else bad('G4 ファイル名に全角/非ASCII文字: ' + base);

// ---- base64 除去版（G2/G3 用）----
const noB64 = src.replace(/data:[a-zA-Z0-9\/+.-]+;base64,[A-Za-z0-9+\/=]+/g, 'data:__B64_STRIPPED__');

// ---- G1 syntax ----
const blocks = [];
const re = /<script[^>]*>([\s\S]*?)<\/script>/g;
let m;
while ((m = re.exec(src)) !== null) blocks.push(m[1]);
if (blocks.length === 0) bad('G1 script ブロックが見つからない');
let synOK = 0;
blocks.forEach((b, i) => {
  try { acorn.parse(b, { ecmaVersion: 2020 }); synOK++; }
  catch (e) { bad('G1 script#' + (i + 1) + ' 構文エラー: ' + e.message); }
});
if (synOK === blocks.length && blocks.length > 0) ok('G1 acorn構文 ' + synOK + '/' + blocks.length + ' ブロックOK');

// ---- G2 __dbg ----
const dbgN = (noB64.match(/__dbg/g) || []).length;
if (dbgN === 0) ok('G2 __dbg 0件');
else bad('G2 __dbg が ' + dbgN + ' 件残っている');

// ---- G3 forbidden APIs ----
const ellipseCalls = (noB64.match(/ctx\.ellipse\s*\(/g) || []).length;
if (ellipseCalls === 0) ok('G3 ctx.ellipse() 呼び出し 0件（ctxEllipse ヘルパー使用）');
else bad('G3 ctx.ellipse() の呼び出しが ' + ellipseCalls + ' 件（ctxEllipse を使うこと）');

const ellipseTernary = (noB64.match(/ctx\.ellipse\s*\?/g) || []).length;
console.log('     （参考: 存在確認三項 ctx.ellipse? は ' + ellipseTernary + ' 件 — 既知の例外）');

const rrN = (noB64.match(/roundRect/g) || []).length;
if (rrN === 0) ok('G3 roundRect 0件');
else bad('G3 roundRect が ' + rrN + ' 件（使用禁止API）');

// ---- result ----
console.log(fail === 0 ? '\n\u2705 ALL GATES PASSED — コミット可' : '\n\u274c ' + fail + ' 件の違反 — コミット禁止');
process.exit(fail === 0 ? 0 : 1);
