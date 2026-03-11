import json
import logging
import argparse
import os
from tqdm import tqdm
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)

# .envファイルをロード
load_dotenv()

# 評価に使用するモデルと設定
MODEL_SETTINGS ={
    "model":"gpt-4o-mini",
    "reasoning_effort": "minimal",#"minimal","low","medium","high" 
    "verbosity": "low" #"low","medium","high"
}


BASIC_ANSWER_SIMILARITY_PROMPT = (
"""
あなたは質問応答の採点官です。
与えられた「質問」と「正しい回答」を踏まえて、「回答」の「正確性」を判定してください。
判定結果は、正確なら"1" 不正確なら"0" のどちらか1語だけを出力してください。

質問: {question}
正しい回答: {reference_answer}
回答: {answer}
""")


def basic_evaluate(questions: list, generated_answers: list, target_answers: list) -> list:

    chat = ChatOpenAI(model=MODEL_SETTINGS["model"], temperature=0, max_tokens=None)

    eval = []
    for question, target_answer, generated_answer in zip(tqdm(questions), target_answers, generated_answers):
        try:
            prompt = BASIC_ANSWER_SIMILARITY_PROMPT.format(
                question=question,
                reference_answer=target_answer,
                answer=generated_answer
            )

            result = chat.invoke(prompt)
            print("Q:", question)
            print("A:", generated_answer)
            print("正解:", target_answer)
            print("評価:", result.content.strip())

            eval.append(int(result.content.strip()))
        except Exception as e:
            logger.warning(f"llm_eval exception: {e}")
            eval.append(-1)
    return eval


def load_qa_results(file_path: str):
    """QA結果のJSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = []
    predicted_answers = []
    correct_answers = []
    success_count = 0
    
    for item in data:
        # successがtrueの場合のみ評価対象とする
        if item.get('success', False):
            success_count += 1
            questions.append(item['question'])
            predicted_answers.append(item['predicted_answer'])
            correct_answers.append(item['correct_answer'])
    
    logging.info(f"評価対象となる質問数: {success_count}")

    return questions, predicted_answers, correct_answers, success_count


def evaluate_references(predicted_refs: list, correct_refs: list) -> tuple[float, list]:
    """
    predicted_refsの中にcorrect_refsのPDFとページが含まれているかを評価し、合致率スコアを返す

    Args:
        predicted_refs: 予測された参照情報のリスト
        correct_refs: 正解の参照情報のリスト

    Returns:
        tuple[float, list]: (合致率スコア, 見つからなかった参照文献のリスト)
    """
    not_found_refs = []
    match_count = 0
    total = len(correct_refs)
    for correct_ref in correct_refs:
        correct_pdf = correct_ref['pdf'].strip("'")
        correct_page = correct_ref['page']

        found = False
        for pred_ref in predicted_refs:
            pred_pdf = pred_ref['pdf'].strip("'")
            pred_page = pred_ref['page']

            if correct_pdf == pred_pdf and correct_page == pred_page:
                found = True
                break

        if found:
            match_count += 1
        else:
            not_found_refs.append({
                'pdf': correct_pdf,
                'page': correct_page
            })

    score = match_count / total if total > 0 else 0.0
    return (score, not_found_refs)

def evaluate_references_full_coverage(predicted_refs: list, correct_refs: list) -> tuple[float, list]:
    """
    predicted_refsの中にcorrect_refsのPDFとページがすべて含まれているかを評価し、
    包含されていれば1、そうでなければ0のスコアを返す

    Args:
        predicted_refs: 予測された参照情報のリスト
        correct_refs: 正解の参照情報のリスト

    Returns:
        tuple[float, list]: (完全一致スコア, 見つからなかった参照文献のリスト)
    """
    predicted_set = {
        (pred_ref['pdf'].strip("'"), pred_ref['page']) for pred_ref in predicted_refs
    }

    not_found_refs = []
    for correct_ref in correct_refs:
        correct_pdf = correct_ref['pdf'].strip("'")
        correct_page = correct_ref['page']

        if (correct_pdf, correct_page) not in predicted_set:
            not_found_refs.append({
                'pdf': correct_pdf,
                'page': correct_page
            })

    score = 1.0 if not not_found_refs else 0.0
    return (score, not_found_refs)

def main(qa_file: str, reference_eval_mode: str):
    
    if not os.path.exists(qa_file):
        print(f"エラー: ファイル '{qa_file}' が見つかりません。")
        return
    
    # results フォルダが存在しない場合は作成
    os.makedirs("results", exist_ok=True)  # srcを除去
    
    # QA結果の読み込み
    questions, predicted_answers, correct_answers, success_count = load_qa_results(qa_file)
    
    if not questions:
        print("評価対象となる質問が見つかりませんでした。")
        return
    
    print(f"\n成功した質問数: {success_count}")
    print("評価を開始します...")
    
    # 評価を実行 
    eval_list = basic_evaluate(questions=questions, generated_answers=predicted_answers, target_answers=correct_answers)

    if reference_eval_mode == "match-rate":
        reference_eval_fn = evaluate_references
    else:
        reference_eval_fn = evaluate_references_full_coverage
    print(f"参照文献評価モード: {reference_eval_mode}")
    
    # QAの結果集計
    total = len(eval_list)
    correct = eval_list.count(1)
    accuracy = correct / total * 100
    
    # 参照文献の評価と集計
    with open(qa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    ref_results = []
    ref_details = []
    for item in data:
        # successがtrueの場合のみ評価対象とする
        if item.get('success', False):
            result, not_found = reference_eval_fn(
                item['predicted_references'], 
                item['correct_references']
            )
            ref_results.append(result)
            ref_details.append({
                'correct_refs': item['correct_references'],
                'predicted_refs': item['predicted_references'],
                'not_found': not_found
            })
    
    # totalを成功した質問数に基づいて計算
    total = len(ref_results)  # successがtrueの項目のみの数
    ref_correct = sum(ref_results)
    ref_accuracy = (ref_correct / total * 100) if total > 0 else 0
    
    # 評価結果をJSONとして構造化
    evaluation_results_json = {
        "model": MODEL_SETTINGS["model"],
        "answer_evaluation": {
            "total_question": total,
            "correct": correct,
            "accuracy": round(accuracy, 2)
        },
        "reference_evaluation": {
            "mode": reference_eval_mode,
            "total_question": total,
            "accuracy": round(ref_accuracy, 2)
        },
        "details": []
    }
    
    # 詳細結果をJSON形式で追加
    for i, (q, p, c, e, ref_r, ref_detail) in enumerate(zip(
        questions, predicted_answers, correct_answers,
        eval_list, ref_results, ref_details)):
        
        detail = {
            "question_number": i + 1,
            "final_evaluation": "correct" if e == 1 else "incorrect",
            "qa_data": {
                "question": q,
                "predicted_answer": p,
                "correct_answer": c
            },
            "reference_evaluation": {
                "result": ref_r,
                "correct_references": [
                    {"pdf": ref["pdf"].strip(), "page": ref["page"]} 
                    for ref in ref_detail["correct_refs"]
                ],
               "predicted_references": [
                    {"pdf": ref["pdf"].strip(), "page": ref["page"]} 
                    for ref in ref_detail["predicted_refs"]
                ],
                "not_found_references": [
                    {"pdf": ref["pdf"], "page": ref["page"]}
                    for ref in ref_detail.get("not_found", [])
                ],
            }
        }
        evaluation_results_json["details"].append(detail)
    
    # JSON形式で結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/evaluation_result_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n評価結果をJSONファイルに保存しました: {output_file}")

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='QAシステムの回答と参照文献の精度を評価します',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--qa-results-file',
        required=True,
        help='評価対象のQA結果JSONファイルパス'
    )
    parser.add_argument(
        '--reference-eval-mode',
        choices=['match-rate', 'full-coverage'],
        default='full-coverage',
        help='参照評価の方式を選択します。match-rateは一致率をスコア化し、full-coverageは完全一致のみを評価します。'
    )
    args = parser.parse_args()

    main(args.qa_results_file, args.reference_eval_mode)
