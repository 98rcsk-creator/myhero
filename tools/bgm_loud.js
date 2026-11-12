#!/usr/bin/env node
/*
 * My HERO BGM の聞こえる大きさ（CLAUDE.md §1-24）
 *   使い方: node tools/bgm_loud.js [曲のID ...]   （省略時は15曲すべて。1曲 数十秒〜2分かかる）
 *   試聴ページ test/bgm_home.html の MUS.render で、音を出さずに曲を計算し、iPhone のスピーカーで聞こえる大きさを出す
 *     ・300Hz より下を急に削る（2段）＋ 1.5kHz より上を +4dB（スマホのスピーカーと、耳の感じ方に近づける）
 *     ・全体＝400ms ごとに区切り、いちばん静かな所（全体より10dB以上小さい区間）を除いた平均（放送の音量の測り方と同じ考え方）
 *     ・最初の12秒／いちばん小さい3秒／最大（音割れは 1.0 以上）／同時に鳴る発音体の数
 *   ねらい（v349）：ステージ -16.0／キャラ選択・ショップ -17.8／ボス -15.5／クリア -16.0dB。ホームは出だしが全体より4dB以内
 *   Playwright（Chromium）を使う。この環境では /opt/node22/lib/node_modules/playwright にある
 */
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
const PAGE = 'file://' + path.resolve(__dirname, '..', 'test', 'bgm_home.html');
const ALL = ['J', 'K', 'S', 'X', 'C', 'W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10'];

(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); let errs = 0;
  p.on('pageerror', x => { errs++; console.log('ERR', x.message); });
  await p.goto(PAGE);
  const ids = process.argv.slice(2).length ? process.argv.slice(2) : ALL;
  for (const id of ids) {
    const r = await p.evaluate(async (id) => {
      const st = await MUS.render(id, null, 1), buf = MUS._buf, OC = window.OfflineAudioContext || window.webkitOfflineAudioContext, oc = new OC(1, buf.length, 44100);
      const src = oc.createBufferSource(); src.buffer = buf; let n = src;
      for (let i = 0; i < 2; i++) { const h = oc.createBiquadFilter(); h.type = 'highpass'; h.frequency.value = 300; h.Q.value = 0.707; n.connect(h); n = h; }
      const sh = oc.createBiquadFilter(); sh.type = 'highshelf'; sh.frequency.value = 1500; sh.gain.value = 4; n.connect(sh); sh.connect(oc.destination); src.start(0);
      const o = await oc.startRendering(), d = o.getChannelData(0), end = Math.floor((st.sec - 2) * 44100);
      const pw = (x0, x1) => { let s = 0; for (let i = x0; i < x1; i++) s += d[i] * d[i]; return s / Math.max(1, x1 - x0); }, db = v => +(10 * Math.log10(v + 1e-12)).toFixed(1);
      const blk = Math.floor(0.4 * 44100), hop = Math.floor(0.1 * 44100), bl = []; for (let x = 0; x + blk <= end; x += hop) bl.push(pw(x, x + blk));
      const a = bl.filter(v => db(v) > -70), m0 = a.reduce((s, v) => s + v, 0) / a.length, g = a.filter(v => db(v) > db(m0) - 10), I = db(g.reduce((s, v) => s + v, 0) / g.length);
      let Q = 99; for (let x = 0; x + 3 * 44100 <= end; x += Math.floor(0.5 * 44100)) Q = Math.min(Q, db(pw(x, x + 3 * 44100)));
      return { I, F: db(pw(Math.floor(0.1 * 44100), Math.min(end, 12 * 44100))), Q, peak: st.peak, voices: st.maxAtOnce };
    }, id);
    console.log(id.padEnd(4), '全体', String(r.I).padStart(6), '| 最初の12秒', String(r.F).padStart(6), '| いちばん小さい3秒', String(r.Q).padStart(6), '| 最大', r.peak, (r.peak >= 1 ? '❌音割れ' : ''), '| 同時', r.voices);
  }
  if (errs) console.log('❌ ページのエラー', errs, '件');
  await b.close(); process.exit(errs ? 1 : 0);
})();
