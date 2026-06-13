"""
Custom LLM-as-Judge Evaluation Script
Replicates RAGAS-style metrics (faithfulness, answer relevancy,
context precision, context recall) using Gemini directly —
avoids dependency conflicts with the ragas package.

Usage: python eval/run_ragas.py
"""
import sys
import os
import json
import time
import re

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.rag_chain import build_rag_chain, create_memory, get_llm, get_cached_retriever


def load_test_questions(path="eval/test_questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_judge(llm, prompt: str) -> float:
    """
    Sends a scoring prompt to Gemini and extracts a float score 0.0-1.0.
    Retries once if parsing fails.
    """
    for attempt in range(2):
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        # Gemini sometimes returns list-of-blocks
        if isinstance(text, list):
            text = "".join(
                b.get("text", "") for b in text if isinstance(b, dict) and b.get("type") == "text"
            )

        match = re.search(r"(\d*\.?\d+)", text)
        if match:
            score = float(match.group(1))
            return max(0.0, min(1.0, score))  # clamp to [0,1]

        time.sleep(1)

    return 0.0  # fallback if parsing fails twice


def score_faithfulness(llm, answer, contexts):
    """Does the answer stick to the given context (no hallucination)?"""
    context_text = "\n\n".join(contexts)
    prompt = f"""You are evaluating an AI assistant's answer for FAITHFULNESS to the provided context.

Context:
{context_text}

Answer:
{answer}

Score from 0.0 to 1.0 how faithful the answer is to the context.
1.0 = every claim in the answer is directly supported by the context.
0.0 = the answer contains significant information not found in the context (hallucination).

Respond with ONLY a number between 0.0 and 1.0."""
    return ask_judge(llm, prompt)


def score_answer_relevancy(llm, question, answer):
    """Does the answer actually address the question asked?"""
    prompt = f"""You are evaluating an AI assistant's answer for RELEVANCY to the question.

Question:
{question}

Answer:
{answer}

Score from 0.0 to 1.0 how relevant and on-topic the answer is to the question.
1.0 = the answer directly and completely addresses the question.
0.0 = the answer is off-topic or doesn't address the question.

Respond with ONLY a number between 0.0 and 1.0."""
    return ask_judge(llm, prompt)


def score_context_precision(llm, question, contexts):
    """Are the retrieved chunks actually relevant to the question (low noise)?"""
    context_text = "\n\n---\n\n".join(contexts)
    prompt = f"""You are evaluating retrieved document chunks for PRECISION.

Question:
{question}

Retrieved chunks:
{context_text}

Score from 0.0 to 1.0 what proportion of these chunks are actually relevant
and useful for answering the question.
1.0 = all chunks are relevant.
0.0 = none of the chunks are relevant (all noise).

Respond with ONLY a number between 0.0 and 1.0."""
    return ask_judge(llm, prompt)


def score_context_recall(llm, ground_truth, contexts):
    """Do the retrieved chunks contain ALL the info needed to produce the ground truth answer?"""
    context_text = "\n\n---\n\n".join(contexts)
    prompt = f"""You are evaluating retrieved document chunks for RECALL.

Expected (ground truth) answer:
{ground_truth}

Retrieved chunks:
{context_text}

Score from 0.0 to 1.0 how much of the information needed to produce the
expected answer is present in these chunks.
1.0 = all necessary information is present.
0.0 = none of the necessary information is present.

Respond with ONLY a number between 0.0 and 1.0."""
    return ask_judge(llm, prompt)


def run_evaluation():
    print("📄 Loading test questions...")
    test_questions = load_test_questions()
    print(f"✅ Loaded {len(test_questions)} questions\n")

    llm = get_llm()
    retriever = get_cached_retriever()

    records = []

    for i, item in enumerate(test_questions, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]
        print(f"[{i}/{len(test_questions)}] {question[:60]}...")

        # Generate answer using the real RAG chain (fresh memory per question)
        memory = create_memory()
        chain = build_rag_chain(memory)
        response = chain.invoke({"question": question})
        answer = response.get("answer", "")

        # Get retrieved chunks
        docs = retriever.invoke(question)
        contexts = [doc.page_content for doc in docs]

        # Score all 4 metrics
        faith = score_faithfulness(llm, answer, contexts)
        time.sleep(1)
        relevancy = score_answer_relevancy(llm, question, answer)
        time.sleep(1)
        precision = score_context_precision(llm, question, contexts)
        time.sleep(1)
        recall = score_context_recall(llm, ground_truth, contexts)
        time.sleep(1)

        print(f"    faithfulness={faith:.2f}  relevancy={relevancy:.2f}  "
              f"precision={precision:.2f}  recall={recall:.2f}")

        records.append({
            "question": question,
            "answer": answer,
            "ground_truth": ground_truth,
            "faithfulness": faith,
            "answer_relevancy": relevancy,
            "context_precision": precision,
            "context_recall": recall,
        })

    # Save detailed CSV
    os.makedirs("eval/results", exist_ok=True)

    import csv
    csv_path = "eval/results/ragas_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"\n✅ Detailed results saved to {csv_path}")

    # Save summary
    summary = {
        "faithfulness": sum(r["faithfulness"] for r in records) / len(records),
        "answer_relevancy": sum(r["answer_relevancy"] for r in records) / len(records),
        "context_precision": sum(r["context_precision"] for r in records) / len(records),
        "context_recall": sum(r["context_recall"] for r in records) / len(records),
        "num_questions": len(records),
    }
    with open("eval/results/ragas_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary saved to eval/results/ragas_summary.json")
    print("\n" + "=" * 50)
    print("📈 EVALUATION SUMMARY")
    print("=" * 50)
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    run_evaluation()