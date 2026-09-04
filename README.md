# Personal Daily Intelligence Report

無料の公開RSSからニュースを取得し、重要性・関連性・前回からの変化を整理したHTML/PDFを毎日作る学習プロジェクトです。**Version 1（Phase 0〜14）は完成済み**です。APIキー、従量課金AI、有料ニュースAPIは使いません。

## Phase 0: 環境確認

- 作業環境: macOS
- 確認したPython: 3.14.2
- 追加料金・APIキー: 不要
- データ取得方法: 公開RSS / Atom
- 保存先: `data/`（JSON）、`output/`（HTML/PDF）、`logs/`（実行ログ）

Python 3.10以降を推奨します。プロジェクト専用の仮想環境 `.venv` を使うため、ほかのPythonプロジェクトとライブラリが混ざりません。

## システム全体の流れ

```text
[公開RSS]
    ↓ 取得
[共通形式へ変換]
    ↓
[期間・カテゴリ・重複・採点]
    ↓
[前日データと比較]
    ↓
[HTMLレポート]
    ↓
[PDF]
    ↓
[GitHub Actionsで毎朝実行]
```

すべての箱をPhaseごとに追加し、Phase 14で自動テストと生成物の検証まで行っています。

## 完成した構成

```text
daily-intelligence-report/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py
│   ├── fetcher.py
│   ├── normalizer.py
│   ├── deduplicator.py
│   ├── classifier.py
│   ├── scoring.py
│   ├── comparator.py
│   ├── signals.py
│   ├── selector.py
│   ├── storage.py
│   ├── pdf_generator.py
│   ├── report_generator.py
│   └── utils.py
├── config/
│   ├── sources.yaml
│   ├── categories.yaml
│   ├── interests.yaml
│   ├── watchlist.yaml
│   └── settings.yaml
├── templates/
│   ├── report.html
│   ├── style.css
│   └── pdf_style.css
├── data/
│   ├── raw/
│   ├── processed/
│   └── history/
├── output/html/ と output/pdf/
├── assets/fonts/
├── logs/
├── tests/
└── .github/workflows/daily_report.yml
```

`.venv/`、`__pycache__/`、`tmp/`は実行環境・一時ファイルなのでGit管理から除外しています。

## Phase 1で作成したファイル

```text
daily-intelligence-report/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── sources.yaml
└── src/
    ├── main.py
    └── fetcher.py
```

| ファイル | 何をするか | なぜ必要か |
|---|---|---|
| `config/sources.yaml` | RSS名・URL・有効/無効・取得件数を管理 | 情報源を変えるたびにPythonを書き換えないため |
| `src/fetcher.py` | RSSを取得し、5項目の辞書へ変換 | 外部データ取得の役割を1か所にまとめるため |
| `src/main.py` | 設定読込、取得、表示を順に実行 | プログラムの入口を分かりやすくするため |
| `requirements.txt` | 必要な無料ライブラリを列挙 | 別のPCでも同じ準備を再現するため |
| `.gitignore` | 仮想環境などをGitの対象外にする | 不要な大容量・自動生成ファイルを登録しないため |
| `README.md` | 学習内容と実行方法を記録 | 半年後でも再開できるようにするため |

## 実行方法

macOS / Linux:

```bash
cd daily-intelligence-report
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
```

Windows PowerShellでは、仮想環境の有効化だけ次のように変わります。

```powershell
.venv\Scripts\Activate.ps1
```

## 正常時の表示例

```text
Personal Daily Intelligence Report - Phase 1
[OK] 日本銀行: 5件
[OK] WHO News: 5件
[OK] NASA: 5件
...
取得結果: 合計 15件 / 失敗 0件
```

RSSの更新状況により件数は変わります。各記事には `title`、`source`、`published_at`、`url`、`summary` が表示されます。

## エラー時の確認

- `[FAILED] 情報源名: ...` が出た場合、その情報源だけ取得に失敗しています。他の情報源の処理は続きます。
- `[ERROR] 設定を読み込めません` が出た場合、`config/sources.yaml` の字下げや記号を確認します。
- `ModuleNotFoundError` が出た場合、仮想環境を有効にして `python -m pip install -r requirements.txt` を再実行します。
- すべて失敗した場合は終了コード1になり、自動化へ進んだ際にも失敗を検出できます。

## Phase 1で学ぶPython

- **変数**: 値に名前を付けます。`articles` は取得した記事一覧です。
- **リスト**: 複数の値を順番に持ちます。`sources` はRSS設定の一覧です。
- **辞書**: `title` のような名前と値を組にして持ちます。ニュース1件を表します。
- **関数**: 処理に名前を付けて再利用します。`fetch_feed()` はRSSを1つ取得します。
- **for**: 情報源や記事を1件ずつ繰り返し処理します。
- **if**: 条件に応じて処理を分けます。無効な情報源を飛ばす場合などに使います。
- **import**: 別ファイルやライブラリの機能を読み込みます。
- **例外処理**: `try` / `except` で取得失敗を受け止め、他のRSSの処理を続けます。
- **pathlib**: Windows・macOSの違いを意識しすぎずにファイル位置を扱います。

## 主なコードの読み方

1. `main.py` の `load_config()` が `sources.yaml` を読みます。
2. `fetch_all_sources()` が有効な情報源を `for` で順番に処理します。
3. `fetch_feed()` が `feedparser` でRSSを読み、5項目の辞書を作ります。
4. 1つの情報源が失敗すると `except` がエラーを記録し、次へ進みます。
5. `display_articles()` がニュースをターミナルへ表示します。

`requests` はRSS本文を安全に取得し、`feedparser` はRSS/Atom形式の違いを吸収します。`PyYAML` は、情報源をPythonコードから分離して編集しやすくするために使います。

## 今回覚えること

1. YAMLに設定を置くと、コードを書き換えず情報源を変更できる。
2. RSSはサイトの更新情報を機械的に取得しやすいXML形式である。
3. ニュース1件は辞書、複数件はリストで表現できる。
4. 関数へ分けると、取得・表示などの役割が読みやすくなる。
5. 例外処理により、1つの失敗で全体を止めずに済む。

## ミニ課題（答えはまだ見ない）

`config/sources.yaml` の `max_items_per_source` を変更し、1つの情報源につき3件だけ表示されるようにしてください。変更後に `python src/main.py` を実行し、合計件数がどう変化するか確認しましょう。

## Phase 2: ニュースデータの標準化

### 今回の目標

情報源ごとに異なる日時や概要の形式をそろえ、すべての記事を同じ12項目の辞書として扱えるようにします。分類・重複判定・採点はまだ行わず、後のPhaseで使う項目には初期値だけを入れます。

### 作成・変更したファイル

| ファイル | 変更内容 | なぜ必要か |
|---|---|---|
| `src/normalizer.py` | 標準化処理を新規作成 | 取得と整形の責任を分けるため |
| `src/fetcher.py` | HTML除去を標準化側へ移動 | 取得処理をRSSの読み込みに集中させるため |
| `src/main.py` | 取得後に標準化を実行 | `取得 → 標準化 → 表示`の順にするため |
| `README.md` | Phase 2の教材を追加 | 学習内容と確認方法を残すため |

### 標準形式

```python
{
    "id": "606db7c410ec0404",
    "title": "記事タイトル",
    "source": "情報源名",
    "published_at": "2026-09-03T05:40:00Z",
    "url": "https://example.com/article",
    "summary": "HTMLタグを除いた概要",
    "category": "",
    "importance_score": 0,
    "relevance_score": 0,
    "keywords": [],
    "duplicate_group": "",
    "is_watchlist": False
}
```

空文字、`0`、空リスト、`False`は「判定済み」という意味ではなく、後のPhaseで更新するための初期値です。

### 処理の流れ

1. `fetcher.py`がRSSから5項目を取得します。
2. `normalize_articles()`が記事を1件ずつ処理します。
3. 余分な空白とHTMLタグを除きます。
4. 公開日時をUTCのISO 8601形式へ統一します。
5. URLから再現可能な記事IDを作ります。URLがない場合はタイトルと情報源を使います。
6. 後のPhase用の7項目へ初期値を入れます。
7. `main.py`が12項目をターミナルへ表示します。

### 新しく学ぶPython

- **リスト内包表記**: `[normalize_article(article) for article in articles]`のように、繰り返しから新しいリストを簡潔に作ります。
- **標準ライブラリ**: Pythonに最初から含まれる機能です。日時、HTML解析、ハッシュ生成に使っています。
- **UTC / ISO 8601**: PCや情報源の時差に左右されにくい共通の日時表現です。末尾の`Z`はUTCを表します。
- **ハッシュ**: 文字列から決まった長さの値を作る仕組みです。今回はURLから安定した記事IDを作ります。
- **初期値**: 後で計算する項目に、現在の状態を表す空文字や`0`を入れます。

### 重要なコードの読み方

- `normalize_text()`は値を文字列にし、改行や連続する空白を1個へそろえます。
- `remove_html()`は`<p>`などのタグを除き、概要本文だけを残します。
- `normalize_published_at()`はRSS日時をUTCへ変換します。読めない日時を勝手に推測せず空欄にします。
- `create_article_id()`は同じURLから同じ16文字のIDを作ります。
- `normalize_article()`は12項目を持つニュース辞書を完成させます。

### 実行方法と正常時の出力

```bash
source .venv/bin/activate
python src/main.py
```

正常時は先頭に`Personal Daily Intelligence Report - Phase 2`と表示され、各記事に12項目が出ます。公開日時が`2026-09-03T05:40:00Z`のような形なら日時の標準化も成功です。

### エラー時の確認

- 日時が空欄: 元RSSの日付形式を`published_at`で確認します。Phase 2では誤った推測を避けるため空欄にします。
- 概要が`概要なし`: 情報源がRSSへ概要を掲載していない場合があり、異常とは限りません。
- RSS自体が`[FAILED]`: Phase 1と同様に、URL・ネット接続・相手サイトの状態を確認します。
- `ModuleNotFoundError`: `.venv`の有効化と`pip install -r requirements.txt`を確認します。

### 今回覚えること

1. 外部データは、処理前に共通形式へそろえると後のコードが単純になる。
2. 取得と標準化を別ファイルにすると、それぞれの役割が明確になる。
3. 日時はUTCへそろえると、異なる国のニュースを比較しやすい。
4. URL由来のIDは、同じ記事を後から識別する助けになる。
5. 未実装の値を推測せず、初期値として明示できる。

### ミニ課題（答えはまだ表示しません）

`normalize_text()`が何をするか試してみましょう。Pythonから`"  AI   news\n today  "`を渡し、結果がどのような文字列になるか確認してください。

## Phase 3: 期間フィルタ・カテゴリ分類

### 今回の目標

標準化した記事から過去48時間以内の記事だけを選び、タイトルと概要のキーワードを使ってカテゴリを決めます。期間と分類ルールはPythonコードではなくYAMLから変更できます。

`Top Intelligence`は後のPhase 6で重要記事を選ぶレポート欄なので、Phase 3の分類先にはしていません。

### 作成・変更したファイル

| ファイル | 何をするか | なぜ必要か |
|---|---|---|
| `config/categories.yaml` | 対象時間、カテゴリ、キーワード、情報源別の初期分類を管理 | Pythonを変更せず分類ルールを調整するため |
| `src/classifier.py` | 期間フィルタとカテゴリ分類を実行 | Phase 3の処理をほかの役割から分離するため |
| `src/main.py` | 標準化後に期間抽出と分類を追加 | 全処理を正しい順番で接続するため |
| `README.md` | Phase 3の教材を追加 | 設定変更と確認方法を残すため |

### 処理の流れ

1. Phase 2までと同じようにRSSを取得・標準化します。
2. 現在時刻から`lookback_hours`を引き、期間の開始時刻を求めます。
3. 公開日時が開始時刻から現在時刻までの記事だけを残します。
4. タイトルと概要から各カテゴリのキーワードを探します。
5. 一致数が最も多いカテゴリを採用します。同数ならYAMLで上にあるカテゴリを優先します。
6. 一致がなければ`source_defaults`、それもなければ`default_category`を使います。
7. 一致したキーワードを記事の`keywords`へ保存します。

### 分類ルールの変更例

対象期間を24時間へ変える場合:

```yaml
lookback_hours: 24
```

キーワードを追加する場合:

```yaml
- name: Medicine / Healthcare
  keywords:
    - antimicrobial resistance
    - 薬剤耐性
```

YAMLでは字下げが構造を表すため、同じカテゴリのキーワードと同じ位置に追加します。

### 新しく学ぶPython

- **`datetime`**: 日時を比較できるPythonの型です。
- **`timedelta`**: 「48時間」のような時間の長さを表します。
- **`None`**: 値が存在しないことを表します。読めない日時に使用します。
- **正規表現**: 文字の検索規則です。短い英単語`AI`が`daily`の一部へ誤一致しないために使います。
- **タプル**: `included, excluded`のように複数の結果をまとめて返せます。
- **引数の初期値**: `now=None`により、通常は現在時刻、テストでは固定時刻を利用できます。

### 重要なコードの読み方

- `parse_iso_datetime()`はISO形式の文字列を、比較可能な日時へ戻します。
- `filter_articles_by_period()`は記事を対象内と対象外の2リストに分けます。
- `contains_keyword()`は英数字を単語単位、日本語を部分一致で探します。
- `classify_article()`はキーワード一致数を比較し、1件のカテゴリを決めます。
- `dict(article)`で元の記事をコピーしてから分類結果を書き込みます。

### 実行方法

```bash
source .venv/bin/activate
python src/main.py
```

今回の実データでは次の結果を確認しました。

```text
RSS取得: 15件 / 情報源の失敗 0件
対象期間: 過去 48時間
対象記事: 10件
期間外または日時不明: 5件
```

記事ごとの`category`と`keywords`に分類結果が表示されれば成功です。取得時刻やRSS更新状況により件数は変わります。

### エラー時の確認方法

- `lookback_hours は1以上`: `categories.yaml`の値が0以下になっていないか確認します。
- `categories の一覧がありません`: YAMLの`categories:`や字下げを確認します。
- 対象記事が0件: RSS取得件数と期間外件数を確認します。記事を取得できていれば正常な場合もあります。
- 想定と違うカテゴリ: 表示された`keywords`を確認し、キーワードの追加・削除・カテゴリ順を調整します。
- 日時不明で除外: 元RSSに公開日時があるか確認します。Phase 3では日時を推測しません。

### 今回覚えること

1. 日時を同じタイムゾーンへそろえると、安全に期間比較できる。
2. 設定をYAMLへ置くと、コードを変更せずルールを調整できる。
3. キーワード一致数で簡単なルールベース分類を作れる。
4. 対象外の記事も数えると、なぜ件数が減ったか確認できる。
5. テスト時刻を固定すると、期間処理を再現可能に確認できる。

### ミニ課題（答えはまだ表示しません）

`config/categories.yaml`へ、Medicine / Healthcareのキーワードとして`antimicrobial resistance`と`薬剤耐性`を追加してください。追加後も`python src/main.py`がエラーなく動くことを確認しましょう。

## Phase 4〜14: Version 1完成まで

以下は各Phaseで追加した役割、重要な読みどころ、確認方法です。コードは「取得」「加工」「出力」の責任を小さな関数へ分け、設定値はYAMLへ置いています。

### Phase 4: 重複検出・グループ化

- 目標: 同じ出来事の記事を削除せず、1つのニュースグループへまとめる。
- ファイル: `src/deduplicator.py`。`difflib.SequenceMatcher`によるタイトル類似度、単語の重なり、カテゴリ、公開時刻を確認します。
- 流れ: 各記事を既存グループと比較し、近ければ統合、違えば新規グループにします。代表記事は情報源の信頼性で選び、`related_articles`と`duplicate_sources`を残します。
- 新しいPython: **集合（set）**は重複しない単語群、**ラムダ式**は短い並べ替え条件を表します。
- 実行・成功: `pytest -q tests/test_deduplicator.py`で成功し、類似2件が`duplicate_count: 2`になります。
- エラー確認: 統合しすぎる場合は`config/settings.yaml`の`title_similarity`を上げます。まとまらない場合は下げます。
- 覚えること: 類似判定には複数条件を使う／元記事を残す／閾値を設定へ分離する。
- ミニ課題: `title_similarity`を0.05だけ上げ、テスト結果が変わらないか確認してください。

### Phase 5: Importance / Relevance Score

- 目標: 世界的重要度と自分との関連度を別々に数値化し、根拠も保存する。
- ファイル: `src/scoring.py`、`config/interests.yaml`、`config/watchlist.yaml`、`config/settings.yaml`。
- 流れ: 信頼性、鮮度、Watch List、複数情報源、重要語、新規性を加減算し、Importanceは0〜10、Relevanceは0〜5に収めます。`score_details`が加点理由です。
- 新しいPython: **`min`/`max`**で数値の範囲を制限し、**辞書の入れ子**で採点内訳を持ちます。
- 実行・成功: `pytest -q tests/test_scoring.py`で、上限と採点根拠のテストが通ります。
- エラー確認: 意外な点数では、JSONの`score_details`と一致キーワードを先に確認します。
- 覚えること: ImportanceとRelevanceは別物／点数には説明可能性が必要／重みはYAMLで変更できる。
- ミニ課題: `interests.yaml`の`high_priority`へ自分の関心語を1つ追加してください。

### Phase 6: 重要ニュース選定

- 目標: 全記事から読む価値の高い記事とカテゴリ別上位を選ぶ。
- ファイル: `src/selector.py`。
- 流れ: Importance、Relevance、公開日時の順で並べ、全体上位とカテゴリ別上位を切り出します。
- 新しいPython: **`sorted(..., key=...)`**は複数の基準で並べ替えます。
- 実行・成功: `python src/main.py`後、HTMLの`TODAY'S TOP INTELLIGENCE`が高得点順になります。
- エラー確認: 件数は`settings.yaml`の`selection`、点数は`score_details`を確認します。
- 覚えること: 採点と選定を分離する／同点時の規則を決める／表示件数は設定にする。
- ミニ課題: `top_count`を5へ変更して生成件数を確認してください。

### Phase 7: JSON履歴保存

- 目標: 取得前のデータ、加工済みデータ、完成レポートの比較用履歴を日付別に保存する。
- ファイル: `src/storage.py`、`data/raw/`、`data/processed/`、`data/history/`。
- 流れ: UTF-8のJSONを一時ファイルへ書き、置換して保存します。破損した最新履歴は飛ばし、前の正常な履歴を探します。履歴はPDF完成後だけ保存します。
- 新しいPython: **JSON**は辞書やリストをファイル化する形式、**原子的置換**は書込途中の破損を避ける方法です。
- 実行・成功: 実行日の3種類のJSONが生成されます。
- エラー確認: JSON破損時はログに警告が残り、前の正常ファイルを使用します。
- 覚えること: rawとprocessedを分ける／履歴名に日付を使う／未完成実行を翌日の基準にしない。
- ミニ課題: `data/processed/日付.json`を開き、`stats`と`articles`を探してください。

### Phase 8: WHAT CHANGED

- 目標: 前回履歴と比べ、新規記事・新規テーマ・記事数増加・重要度上昇を抽出する。
- ファイル: `src/comparator.py`。
- 流れ: ID、キーワード、カテゴリ別件数、テーマ別最大重要度を前回と比較し、説明文を作ります。初回は比較基準がない旨を明記します。
- 新しいPython: **辞書集計**はカテゴリやキーワードをキーに件数・最大値を蓄積します。
- 実行・成功: 2回分の異なる履歴があれば`WHAT CHANGED?`へ差分が表示されます。
- エラー確認: 同日ファイルは比較対象外です。初日は差分なしが正常です。
- 覚えること: 差分には基準が必要／同じ日を自己比較しない／ルールで説明可能にする。
- ミニ課題: テスト用の前日JSONへ記事を1件追加し、変化の種類を予想してください。

### Phase 9: SIGNALS

- 目標: `TREND UP`、`NEW TOPIC`、`MULTIPLE SOURCES`、`HIGH PRIORITY`を単純なルールで表示する。
- ファイル: `src/signals.py`。
- 流れ: 変化データと記事のグループ数・重要度を確認し、重複しないシグナル一覧を作ります。
- 新しいPython: **早期continue**は条件外の処理を飛ばし、読みやすくします。
- 実行・成功: `pytest -q tests/test_history_and_signals.py`で複数情報源と高重要度を検出します。
- エラー確認: シグナルが多すぎる場合は`settings.yaml`の閾値と最大件数を調整します。
- 覚えること: シグナルは結論ではなく注意喚起／根拠を本文に残す／上限を設ける。
- ミニ課題: `high_priority_threshold`を1上げて表示差を確認してください。

### Phase 10: HTMLレポート

- 目標: 7セクションを読みやすい1つのHTMLへまとめる。
- ファイル: `src/report_generator.py`、`templates/report.html`、`templates/style.css`。
- 流れ: Pythonがテンプレート用辞書を作り、Jinja2が値を安全にエスケープしてHTMLへ埋め込みます。
- 新しいPython: **テンプレート**はレイアウトとデータを分離します。**autoescape**は記事中のHTMLを命令として実行しない安全機能です。
- 実行・成功: `output/html/daily-intelligence-日付.html`をブラウザで開き、各セクションとリンクを確認します。
- エラー確認: 内容が空ならprocessed JSON、見た目ならCSS、置換されない記号ならテンプレート変数を確認します。
- 覚えること: データと表示を分ける／外部文字列はエスケープする／HTMLはPDFの元にもなる。
- ミニ課題: `style.css`のアクセント色を1か所変更してください。

### Phase 11: A4 PDF

- 目標: HTML/CSSから、A4・余白・ページ番号・日本語フォント付きPDFを作る。
- ファイル: `src/pdf_generator.py`、`templates/pdf_style.css`、`assets/fonts/`。
- 流れ: xhtml2pdfで本文を作り、pypdf/ReportLabで`Page x / y`を重ねます。Noto Sans JPを同梱するためOSのフォントに依存しません。
- 新しいPython: **バイナリファイル**はPDFやフォントのような文字以外のファイル、**コールバック関数**は画像やフォントのURLを実ファイルへ解決します。
- 実行・成功: PDFがA4で開き、日本語、URL、情報源、作成日時、全ページの番号を確認できます。
- エラー確認: `PDF生成に失敗`では依存関係とフォントファイルを確認します。ライセンスは`assets/fonts/OFL.txt`です。
- 覚えること: HTML→CSS→PDFはレイアウト修正が容易／フォント埋込が再現性を上げる／見た目もテスト対象。
- ミニ課題: `pdf_style.css`の本文サイズを0.5ptだけ変え、改ページへの影響を確認してください。

### Phase 12: GitHub Actions

- 目標: 毎朝06:30 JSTにテストと生成を行い、成果物を30日間Artifactに保存する。
- ファイル: `.github/workflows/daily_report.yml`。
- 流れ: checkout→Python 3.12→依存導入→pytest→生成→Artifact→成功時だけ履歴をcommit/pushします。手動実行も可能です。
- 新しい概念: **CI**はクラウド上で同じ処理を自動実行する仕組み、**cron**は定時実行の時刻表です。GitHub ActionsのcronはUTCなので`30 21 * * *`が翌06:30 JSTです。
- 実行・成功: GitHubのActions画面から`Run workflow`を実行し、全stepが緑、Artifactに`output/ data/ logs/`があれば成功です。
- エラー確認: `Actions`ログの最初に赤くなったstepを開きます。リポジトリのWorkflow permissionsは書込許可が必要です。
- 覚えること: ローカルテスト後に生成／成功時だけ履歴保存／ArtifactとGit履歴は役割が違う。
- ミニ課題: 定刻は変えず、手動実行で1回動作確認してください。

### Phase 13: ログ・エラー処理

- 目標: 一部RSS障害では続行し、全滅やPDF失敗では終了コード1と理由を残す。
- ファイル: `src/utils.py`、`src/fetcher.py`、`src/main.py`、`logs/`。
- 流れ: 日付別ログへSTART、取得結果、件数、HTML/PDF、COMPLETEを記録します。1ソースの例外は一覧へ集め、すべて0件だけ全体失敗にします。
- 新しいPython: **logging**は時刻と重要度付きの記録、**終了コード**は自動化へ成功/失敗を伝える数値です。
- 実行・成功: `logs/日付.log`の末尾が`COMPLETE`です。
- エラー確認: `REPORT FAILED`直前の例外、または`FETCH FAILED`の情報源を確認します。
- 覚えること: 失敗を握りつぶさない／部分障害と全体障害を分ける／ログは再現調査の入口。
- ミニ課題: 1つのsourceを一時的に`enabled: false`にし、残りで生成できるか確認してください。

### Phase 14: テスト・PDCA

- 目標: 標準化、分類、重複、採点、履歴、差分、Signals、HTML、PDF、設定、自動化を再現可能に確認する。
- ファイル: `tests/`。pytestの小さなテストに分割しています。
- 流れ: `pytest -q`→実データ生成→JSON構造確認→PDFの文字・A4・ページ番号確認→全ページ画像化して目視、の順で確認します。
- 新しいPython: **fixture**は各テストの準備を共通化し、**assert**は期待結果を機械的に検査します。
- 実行・成功: すべて`passed`、mainが終了コード0、ログ末尾が`COMPLETE`、PDF目視に欠落・重なり・文字化けがなければ完了です。
- エラー確認: 最初に失敗したassertを読み、入力・期待値・実際値のどこが違うか切り分けます。
- 覚えること: 正常系と異常系を試す／コードだけでなく成果物も検証する／修正後は回帰テストする。
- ミニ課題: `tests/test_classifier.py`へ、自分で追加したキーワードの分類テストを1件書いてください。

## 設定の変え方

| 設定 | ファイル | 主な変更箇所 |
|---|---|---|
| 情報源 | `config/sources.yaml` | `url`、`reliability`、`enabled` |
| 対象時間・分類 | `config/categories.yaml` | `lookback_hours`、カテゴリ、キーワード |
| 自分の関心 | `config/interests.yaml` | `high/medium/low_priority` |
| 継続監視 | `config/watchlist.yaml` | テーマ名とキーワード |
| 採点・選定・閾値 | `config/settings.yaml` | `scoring`、`selection`、`signals` |

YAMLは字下げが意味を持ちます。変更後は必ず`pytest -q`を実行してください。

## レポートの見方

1. `EXECUTIVE SUMMARY`で全体像をつかむ。
2. `TODAY'S TOP INTELLIGENCE`で点数、理由、情報源、原文URLを確認する。
3. `WHAT CHANGED?`で前回との差を確認する。初回は基準なしと表示される。
4. `WATCH LIST`と`SIGNALS`は注意喚起として使い、原文で判断する。
5. `TODAY'S TAKEAWAYS`を、その日に覚える短い一覧として使う。

このVersion 1の概要はRSS提供文を機械的に整形したもので、生成AIによる事実確認や医学・投資判断は行いません。重要な判断では必ず原文と一次情報を確認してください。

## トラブルシューティング

- `ModuleNotFoundError`: `.venv`を有効化し、`python -m pip install -r requirements.txt`を再実行。
- RSSが一部失敗: ログのURLを確認。残りの情報源でレポートが作られれば設計どおりです。
- RSSが全滅: ネット接続とURLを確認。空のレポートは作らず終了コード1になります。
- 記事が0件: `lookback_hours`とRSSの公開日時を確認。
- 分類・点数が不自然: processed JSONの`keywords`と`score_details`を確認。
- PDF文字化け: `assets/fonts/NotoSansJP-Regular.ttf`が存在するか確認。
- 前回比較が出ない: 異なる日付の正常な`data/history/*.json`が必要です。
- Actionsでpush失敗: Settings → Actions → GeneralのWorkflow permissionsとブランチ保護を確認。

## 一括確認コマンド

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
python src/main.py
```

成功時はターミナルに生成した6ファイル、ログ末尾に`COMPLETE`が表示されます。
