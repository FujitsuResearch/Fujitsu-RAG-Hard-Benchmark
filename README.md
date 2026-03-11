# Fujitsu RAG Hard Benchmark†

† RAG: Retrieval-Augmented Generation

This is the benchmark dataset introduced in the AAAI 2026 workshop paper
"Overcoming the 'Impracticality' of RAG: Proposing a Real-World Benchmark and Multi-Dimensional Diagnostic Framework."

## Data layout

- `dataset/FJ_KGQA_Hard.yaml`: annotation data (100 questions)
- `dataset/DL_URL.csv`: list of PDF download sources (index, file name, URL)
- `dataset/PDFs`: source PDFs (some included. Items listed in `dataset/DL_URL.csv` should be downloaded and placed by the user)
- `evaluate/`: evaluation scripts and samples
- `pyproject.toml`, `poetry.lock`: dependencies for the evaluation scripts

## Obtaining PDFs

For PDFs listed in `dataset/DL_URL.csv`, download them from each URL and place them in `dataset/PDFs`. If a file already exists, you do not need to download it again. Please follow the license and terms of use of each PDF distributor.

## Annotation format (`dataset/FJ_KGQA_Hard.yaml`)

The YAML file consists of a `tasks` array, and each element represents one QA pair and its evidence.

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

This YAML snippet is intentionally abbreviated. Other diagnostic metrics under `Reasoning Complexity`, `Retrieval Difficulty`, `Source Structure & Modality`, and `Explainability Requirement` are omitted here for readability.

### Field meanings

- `no.`: question ID (string)
- `question`: question text
- `answer`: correct answer (based on the evidence)
- `question_type`: type of question (e.g., Yes/No, Factoid, Definition/Description)
- `retrieval_level`: difficulty of evidence retrieval (Easy/Medium/Hard)
- `answer_level`: difficulty of answering (Easy/Medium/Hard)
- `answer_skill`: required skill or reading operation
- `tag`: media type of evidence (figure/table/text, etc.; multiple possible)
- `grading_criteria`: scoring criteria or additional constraints (may be empty)
- `rationales`: array of evidence entries
  - `file_name`: referenced PDF file name (under `dataset/PDFs`)
  - `pages`: array of referenced pages
    - `number`: page number (1-based)
    - `view`: coordinate system size (typically normalized to 100x100)
    - `bounding_boxes`: rectangles for evidence spans (may be empty)
      - `top`, `left`, `width`, `height`: rectangle position and size in `view` coordinates (origin is top-left)

### Diagnostic metadata fields

Each task also contains diagnostic metadata blocks for multi-dimensional analysis:

- `Reasoning Complexity`
- `Retrieval Difficulty`
- `Source Structure & Modality`
- `Explainability Requirement`

Each metric under those blocks has the following schema:

```yaml
<block_name>:
  <metric_name>:
    value: <label>
```

- `value`: label assigned to that QA item for the metric
- Allowed labels for each metric are documented below

#### Label definitions

`Reasoning Complexity`

| Metric | Allowed labels (`value`) |
|---|---|
| `Reasoning Depth (Multi-step Reasoning)` | `single`, `multi` |
| `Quantitative Operation` | `false`, `true` |
| `Negation Question` | `false`, `true` |
| `Cause and Effect` | `false`, `true` |
| `Comparison (and Conditional Judgment)` | `false`, `true` |
| `Temporal Specification` | `false`, `true` |
| `Type of Output Processing` | `summary`, `trans`, `list` |

`Retrieval Difficulty`

| Metric | Allowed labels (`value`) |
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

| Metric | Allowed labels (`value`) |
|---|---|
| `Tables/Charts` | `false`, `true` |
| `Complex Layout` | `false`, `true` |
| `Specific Area Reference` | `false`, `true` |
| `Logical Nesting` | `false`, `true` |
| `Large Enumeration` | `false`, `true` |
| `Redundancy` | `false`, `true` |

`Explainability Requirement`

| Metric | Allowed labels (`value`) |
|---|---|
| `Strictness of Evidence Presentation` | `no-evidence`, `hier-ref`, `coord-ref`, `multi-ref` |

## Evaluation tools

- `evaluate/evaluate_qa.py`: evaluation script for QA and references
- `evaluate/sample.json`: sample input format
- `evaluate/.env.example`: example `OPENAI_API_KEY` setting
- `results/`: output directory for evaluation results (created on run)

### Usage

1. Copy `evaluate/.env.example` to `evaluate/.env` and set `OPENAI_API_KEY`
2. Edit `MODEL_SETTINGS` in `evaluate/evaluate_qa.py` to select the model
3. Install dependencies: `poetry install`
4. Run evaluation: `python evaluate/evaluate_qa.py --qa-results-file evaluate/sample.json --reference-eval-mode full-coverage`

`--reference-eval-mode` can be set to `match-rate` (match rate) or `full-coverage` (only exact matches).

### Evaluation JSON format

Use the same structure as `evaluate/sample.json`. Only items with `success` set to `true` are evaluated.

- `question`: question text
- `predicted_answer`: generated answer
- `correct_answer`: correct answer
- `predicted_references`: predicted references (array; each element has `pdf` and `page`)
- `correct_references`: correct references (array; each element has `pdf` and `page`)
- `success`: evaluation flag

Make sure the `page` type is consistent between `predicted_references` and `correct_references`
(mixing strings and numbers is treated as a mismatch).

## License

See the ["TERMS_OF_USE"](TERMS_OF_USE.md) for details. PDFs must be used according to the licenses of their distributors.
