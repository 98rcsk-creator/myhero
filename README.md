# My HERO — Claude Code 開発リポジトリ

iPhone Safari / Instagram内蔵ブラウザで動く、単一HTMLファイルの子ども向け2D横スクロールアクション。
顔写真で自分をキャラにできる「マイヒーロー」機能が看板。

## 構成

```
myhero/
├── CLAUDE.md              ← 開発ルールブック（Claude Codeが毎セッション自動で読む・唯一の正本）
├── README.md              ← このファイル
├── index.html             ← 公開用コピー（GitHub Pages がこれを配信。リリース時に game/ からコピー）
├── docs/
│   ├── SPEC.md            ← 仕様・現状・地雷・未検証リスト・ロードマップ（作業用の正本）
│   ├── LEGACY_hikitsugi_v234c.md ← 旧引継書アーカイブ（読み取り専用・v210〜v234の全経緯と根拠）
│   ├── CHANGELOG.md       ← 変更履歴
│   ├── TODO.md            ← TODO・アイデアのメモ
│   └── DEPLOY.md          ← 公開のしくみと手順（ユーザー向け・初心者向け説明）
├── game/
│   └── my_hero.html       ← ゲーム本体（開発はこちらが本体）
└── tools/
    ├── check.js           ← コミット前ゲート（構文・禁止API・__dbg）
    ├── render_bg.js       ← 背景の描画コール計測・NaN検出・PNG描き出し
    └── package.json
```

## 公開URL

https://98rcsk-creator.github.io/myhero/

GitHub Pages は **main ブランチのルート `index.html`** を配信する。
開発は `game/my_hero.html` で行い、リリース時に `cp game/my_hero.html index.html` で同期する（CLAUDE.md §8-5）。

## 初回セットアップ

```bash
cd tools && npm install && cd ..
```

- Node 18+ 推奨。`canvas` のビルドが環境依存で失敗しても、`check.js` と `render_bg.js` の計測・NaN検出は動く（PNG描き出しだけスキップされる）。

## テストモード（実機確認用）

URLに `?test=1`（または `#test`）を付けて開くと、実機確認を楽にするモードになる。

```
通常   https://98rcsk-creator.github.io/myhero/
テスト https://98rcsk-creator.github.io/myhero/?test=1
```

- 全10ワールドが最初から選べる／所持金 99,999G／右上に `TEST` バッジ
- **セーブは本番と完全に別**（キー接頭辞 `tk_`）。テストで何をしても本番データは汚れない
- 通常URLでは分岐に一切入らないため、本番の挙動は不変
- 触る場所は `TEST_MODE` と `store` の `PFX`

## 自動チェック（GitHub Actions）

PR を出すたび／main に入るたびに `.github/workflows/check.yml` が走り、
GitHub のクラウド上で出荷前ゲートを自動実行する（パソコン不要）。

- `node tools/check.js game/my_hero.html`（構文・禁止API・`__dbg`）
- `node tools/check.js index.html`
- `game/my_hero.html` と `index.html` が同一かの照合（§8-5 の公開フローの取りこぼし防止）

落ちると PR に赤い ✗ が出るので、**マージ前に気づける**。公開リポジトリなので実行は無料。

## 日々のワークフロー

1. `docs/SPEC.md` の §未検証 と §ロードマップ を見てテーマを1つ選ぶ（**1コミット＝1テーマ**）
2. 実装（`CLAUDE.md` §1 実装前ゲート → §2 実装規約）
3. `node tools/check.js game/my_hero.html` — 通らない状態はコミット禁止
4. 背景・描画を触ったら `node tools/render_bg.js` — 予算超過とNaNを機械判定、`tools/out/` のPNGを目視
5. `docs/SPEC.md` の該当箇所（現状・パラメータ表・未検証）を**同じコミットで**更新
6. コミット。バージョンを進めるなら `git tag vNNN`
7. 実機確認用ファイルを書き出してユーザーに渡す：
   `cp game/my_hero.html /どこか/my_hero_vNNN.html`（**ファイル名は半角英数字のみ**）
   確認依頼には「どの画面で・何を・どうなっていればOKか」を明記

## 絶対に忘れないこと

- **実機（ユーザーのiPhone）が唯一の真実。** ヘッドレスで通っても実機確認まで「未検証」。
- 単一HTMLファイルが配布物。**分割するなら build スクリプトで byte-perfect に再結合できる形にしてから**（過去に build.py + MD5照合の運用実績あり）。
- 行番号をどこにも書かない。関数名・変数名で参照する。
- 詳しい経緯・過去の失敗の全記録は `docs/LEGACY_hikitsugi_v234c.md`（そこの行番号はv234時点のもので現在は無効）。
