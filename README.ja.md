# Fujitsu RAG Hard Benchmark†

† RAG: Retrieval-Augmented Generation

AAAI2026 のワークショップで発表の論文
Overcoming the ‘Impracticality’ of RAG: Proposing a Real-World Benchmark and Multi-Dimensional Diagnostic Framework
で紹介しているベンチマークデータセットです。

[本ベンチマークデータセットについてのブログはこちら](https://blog.fltech.dev/entry/2026/03/11/RAG-Hard-Benchmark-ja)

## データ構成

- `dataset/FJ_KGQA_Hard.yaml`: アノテーションデータ (全 100 問)
- `dataset/DL_URL.csv`: PDF のダウンロード先一覧 (項番, ファイル名, URL)
- `dataset/PDFs`: 参照元 PDF (一部同梱。`dataset/DL_URL.csv` に記載されたものはユーザーが取得して配置)
- `evaluate/`: 評価スクリプトとサンプル
- `pyproject.toml`, `poetry.lock`: 評価用スクリプトの依存関係

## PDF の入手

`dataset/DL_URL.csv` に記載された PDF は、各 URL からユーザーがダウンロードして `dataset/PDFs` に配置して使用してください。既に存在するファイルは再取得の必要はありません。PDF は各配布元のライセンスや利用条件に従ってください。

## アノテーション形式 (`dataset/FJ_KGQA_Hard.yaml`)

YAML は `tasks` 配列で構成され、各要素が 1 問の QA ペアと根拠情報を表します。

```yaml
tasks:
- no.: "1"
  question: ...
  answer: ...
  question_type: Yes/No
  retrieval_level: Easy
  answer_level: Easy
  answer_skill: 記載通りに回答
  tag: テキスト
  grading_criteria: ""
  rationales:
  - file_name: sample.pdf
    pages:
    - number: 2
      view:
        width: 100
        height: 100
      bounding_boxes:
      - top: 30.82
        left: 0.25
        width: 22.75
        height: 32.57
  Reasoning Complexity:
    Reasoning Depth (Multi-step Reasoning):
      value: multi
```

このYAMLスニペットは意図的に簡略化しています。可読性のため、`Reasoning Complexity` 配下の他指標および `Retrieval Difficulty`、`Source Structure & Modality`、`Explainability Requirement` はここでは省略しています。

### フィールドの意味

- `no.`: 問題 ID (文字列)
- `question`: 質問文
- `answer`: 正解 (参照根拠に基づく回答)
- `question_type`: 質問のタイプ (例: Yes/No, Factoid, Definition/Description など)
- `retrieval_level`: 根拠検索の難易度 (Easy/Medium/Hard)
- `answer_level`: 回答の難易度 (Easy/Medium/Hard)
- `answer_skill`: 必要なスキルや読み取り作業の種類
- `tag`: 根拠の媒体種別タグ (図/表/テキストなど。複数の場合あり)
- `grading_criteria`: 採点基準や補足条件 (空文字の場合あり)
- `rationales`: 根拠情報の配列
  - `file_name`: 参照する PDF ファイル名 (`dataset/PDFs` 内)
  - `pages`: 参照ページの配列
    - `number`: ページ番号 (1 始まり)
    - `view`: 座標系のサイズ (通常は 100x100 の正規化座標)
    - `bounding_boxes`: 根拠箇所の矩形配列 (空の場合あり)
      - `top`, `left`, `width`, `height`: `view` 座標系での矩形位置と大きさ (原点は左上)

### 診断メタデータ項目

各タスクには、多面的な分析用の診断メタデータブロックも含まれます。

- `Reasoning Complexity`
- `Retrieval Difficulty`
- `Source Structure & Modality`
- `Explainability Requirement`

これらの各ブロック配下の指標は、次のスキーマで記録されています。

```yaml
<block_name>:
  <metric_name>:
    value: <label>
```

- `value`: その設問に付与された当該指標のラベル値
- 各指標で使うラベルの種類は以下の表を参照してください

#### ラベル定義

`Reasoning Complexity`

| 指標 | `value` の取りうる値 |
|---|---|
| `Reasoning Depth (Multi-step Reasoning)` | `single`, `multi` |
| `Quantitative Operation` | `false`, `true` |
| `Negation Question` | `false`, `true` |
| `Cause and Effect` | `false`, `true` |
| `Comparison (and Conditional Judgment)` | `false`, `true` |
| `Temporal Specification` | `false`, `true` |
| `Type of Output Processing` | `summary`, `trans`, `list` |

`Retrieval Difficulty`

| 指標 | `value` の取りうる値 |
|---|---|
| `multi-document` | `false`, `true` |
| `multi-chunk` | `false`, `true` |
| `Low Locality` | `false`, `true` |
| `Remote Reference` | `false`, `true` |
| `Document Volume` | `<1000p`, `>=1000p` |
| `Chunk Size` | `<=511tok`, `>=512tok` |
| `Abstraction Discrepancy` | `false`, `true` |
| `Vocabulary Mismatch` | `false`, `true` |

`Source Structure & Modality`

| 指標 | `value` の取りうる値 |
|---|---|
| `Tables/Charts` | `false`, `true` |
| `Complex Layout` | `false`, `true` |
| `Specific Area Reference` | `false`, `true` |
| `Logical Nesting` | `false`, `true` |
| `Large Enumeration` | `false`, `true` |
| `Redundancy` | `false`, `true` |

`Explainability Requirement`

| 指標 | `value` の取りうる値 |
|---|---|
| `Strictness of Evidence Presentation` | `no-evidence`, `hier-ref`, `coord-ref`, `multi-ref` |

## 評価ツール

- `evaluate/evaluate_qa.py`: QA と参照文献の評価スクリプト
- `evaluate/sample.json`: 入力フォーマットのサンプル
- `evaluate/.env.example`: `OPENAI_API_KEY` 設定例
- `results/`: 評価結果の出力先 (実行時に自動生成)

### 使い方

1. `evaluate/.env.example` を `evaluate/.env` にコピーし、`OPENAI_API_KEY` を設定
2. `evaluate/evaluate_qa.py` の `MODEL_SETTINGS` を直接書き換えて使用するモデルを設定
3. 依存関係のインストール: `poetry install`
4. 評価実行: `python evaluate/evaluate_qa.py --qa-results-file evaluate/sample.json --reference-eval-mode full-coverage`

`--reference-eval-mode` は `match-rate` (一致率) と `full-coverage` (完全一致のみ) から選択できます。

### 評価用 JSON 形式

`evaluate/sample.json` と同じ構造で、要素は以下のキーを持ちます。`success` が `true` の要素のみが評価対象になります。

- `question`: 質問文
- `predicted_answer`: 生成回答
- `correct_answer`: 正解
- `predicted_references`: 予測参照 (配列、各要素は `pdf` と `page`)
- `correct_references`: 正解参照 (配列、各要素は `pdf` と `page`)
- `success`: 評価対象フラグ

`page` の型は `predicted_references` と `correct_references` で揃えてください (文字列/数値の混在は不一致扱いになります)。

## ライセンス

詳細は ["TERMS_OF_USE"](TERMS_OF_USE.md) を参照してください。PDF は配布元のライセンスに従って利用してください。
