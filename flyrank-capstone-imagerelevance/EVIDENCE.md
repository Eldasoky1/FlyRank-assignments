# EVIDENCE — AI Image Understanding & Content Matching Engine

Each requirement has one pasted proof (offline).

## 1. Vision structured output (schema-validated, low-confidence flagged not guessed)
```
test_mock_vision_returns_valid_result PASSED   # VisionResult, category=fox, confidence 0-1
test_mock_vision_confidence_and_no_guess_flag PASSED
test_vision_requires_api_key_for_gemini PASSED
```
Every describe() returns a Pydantic `VisionResult`; low confidence is an explicit flag.

## 2. Semantic embeddings + similarity ranking
```
test_embed_is_unit_vector PASSED
test_similar_tokens_rank_higher PASSED
test_matcher_ranks_same_category_first PASSED
```
50-image corpus, 5 categories, cosine ranking.

## 3. Mismatch guard (reject wrong match with explanation, e.g. wolf vs fox)
Manual proof — low-confidence wolf result:
```
guard result: {'image_id': 'wolf-01', 'score': 0.866, 'category': 'wolf',
               'confidence': 0.3, 'accepted': False,
               'reason': 'low confidence; not guessing'}
```
Eval also rejected a near-wrong match with `category mismatch: vision=deer, corpus=bear`:
```
test_mismatch_guard_rejects_confusable PASSED
test_match_accepts_high_confidence_same_category PASSED
```

## 4. Background batch jobs: retries + progress + per-call cost
```
test_batch_job_processes_and_tracks_cost PASSED   # 8 processed, cost_micro_cents > 0
test_job_retries_on_provider_error PASSED        # retries, completed_with_errors
```

## 5. Review API (approve / reject / inspect why)
```
test_review_submit_decision_explain PASSED
test_reject_decision PASSED
```
`GET /review/{image_id}` returns match + vision + guard `why`.

## 6. Labeled eval set measuring top-1 precision
Real run (mock provider):
```
eval: {'labeled_count': 25, 'accepted': 24, 'rejected': 1,
       'rejected_reasons': {'category mismatch: vision=deer, corpus=bear': 1},
       'correct': 24, 'wrong': 0, 'top1_precision': 1.0}
test_eval_reports_precision PASSED
```

## 7. Corpus size
```
test_corpus_size_and_categories PASSED   # >=40 images, 5 categories, >=8 each
test_corpus_ids_are_global_unique PASSED
```

## 8. Full offline suite
```
17 passed, 8 warnings in 0.94s
```
No API keys or network required (mock provider).
