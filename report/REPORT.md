# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Việt Dũng
**Nhóm:** C401-C1
**Ngày:** 10-4-2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn văn bản có cosine similarity cao nghĩa là embedding vectors của chúng chỉ cùng hướng trong không gian nhiều chiều, tức là chúng mang ngữ nghĩa gần nhau dù có thể dùng từ ngữ khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Python is a programming language used for AI."
- Sentence B: "Python is widely used in machine learning development."
- Tại sao tương đồng: Cả hai đều nói về Python trong lĩnh vực AI/ML, chia sẻ chủ đề và ngữ cảnh giống nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Vector databases store embeddings for search."
- Sentence B: "The weather in Hanoi is hot today."
- Tại sao khác: Hai câu thuộc domain hoàn toàn khác nhau (kỹ thuật vs thời tiết), không chia sẻ ngữ nghĩa nào.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector (hướng), không phụ thuộc vào độ dài (magnitude). Với text embeddings, hai đoạn văn bản cùng chủ đề nhưng khác độ dài vẫn có hướng giống nhau, trong khi Euclidean distance sẽ bị ảnh hưởng bởi sự khác biệt về magnitude, dẫn đến kết quả sai lệch.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`. Chunk count tăng vì step (khoảng cách giữa các chunk) nhỏ hơn. Overlap nhiều hơn giúp giữ context liên tục giữa các chunks — nếu một ý bị cắt ở ranh giới chunk A, nó vẫn xuất hiện ở đầu chunk B, giảm rủi ro mất thông tin khi retrieval.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Hệ thống hỗ trợ học tập và tra cứu quy trình khóa học "AI Thực Chiến" (VinUni A20).

**Tại sao nhóm chọn domain này?**
Nhóm chọn bộ tài liệu từ Day 02 đến Day 07 vì đây là nguồn dữ liệu thực tế, có cấu trúc rõ ràng (gồm mục tiêu, timeline, tiêu chí chấm điểm và hướng dẫn kỹ thuật). Việc xây dựng RAG trên bộ dữ liệu này giúp học viên nhanh chóng tra cứu các yêu cầu bài tập (deliverables), thời hạn (deadlines) và các bước cài đặt môi trường mà không cần đọc thủ công toàn bộ các file Markdown.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự (Thực tế) | Metadata đã gán |
|---|---|---|---|---|
| 1 | day02.md | Tài liệu Lab Ngày 2 | 6,666 | day: "02", topic: "problem_statement" |
| 2 | day03.md | Tài liệu Lab Ngày 3 | 2,352 | day: "03", topic: "agent_implementation" |
| 3 | day05.md | Tài liệu Lab Ngày 5 | 12,393 | day: "05", topic: "product_design" |
| 4 | day06.md | Tài liệu Lab Ngày 6 | 17,091 | day: "06", topic: "hackathon" |
| 5 | day07.md | Tài liệu Lab Ngày 7 | 7,609 | day: "07", topic: "embedding_rag" |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|---|---|---|---|
| day | String | "02", "06", "07" | Giúp giới hạn phạm vi tìm kiếm khi người dùng hỏi về một ngày học cụ thể (ví dụ: "Deadline nộp bài Ngày 5 là khi nào?"). |
| topic | String | "hackathon", "logic" | Giúp phân loại nội dung giữa phần lý thuyết thiết kế và phần thực hành lập trình, giúp hàm `search_with_filter` trả về kết quả chính xác hơn theo ngữ cảnh. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| day02 | FixedSizeChunker | 12 | 460 | Đúng |
| day02 | SentenceChunker | 7 | 788 | Đúng |
| day02 | RecursiveChunker | 16 | 344 | Đúng |
| day03 | FixedSizeChunker | 5 | 467 | Đúng |
| day03 | SentenceChunker | 9 | 257 | Đúng |
| day03 | RecursiveChunker | 7 | 332 | Đúng |
| day05 | FixedSizeChunker | 22 | 481 | Đúng |
| day05 | SentenceChunker | 14 | 752 | Đúng |
| day05 | RecursiveChunker | 31 | 340 | Đúng |

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> Strategy này hoạt động bằng cách thử tách văn bản theo danh sách các dấu phân cách ưu tiên từ lớn đến nhỏ: đoạn văn (\n\n), dòng (\n), câu (. ), từ ( ) và cuối cùng là ký tự rỗng (""). Nó giúp giữ được cấu trúc ngữ nghĩa lớn nhất có thể trước khi phải chia nhỏ thêm để thỏa mãn giới hạn `chunk_size`.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Vì các file này có cấu trúc phân cấp (Header #, ##, ###), việc sử dụng RecursiveChunker với các dấu phân cách như `["\n### ", "\n## ", "\n# ", "\n\n", ". "]` giúp giữ nguyên các đoạn hướng dẫn hoặc tiêu chí chấm điểm đi liền với nhau, tránh bị mất ngữ cảnh quan trọng khi một lệnh code hoặc một định nghĩa bị cắt giữa chừng.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| day02 | best baseline (by_sentences) | 13 | 512 | Đúng |
| | **của tôi (recursive)** | 16 | 344 | Better (more granular structure for lists) |
| day03 | best baseline (by_sentences) | 9 | 257 | Đúng |
| | **của tôi (recursive)** | 40 | 57 | Rất tốt (tách nhỏ được từng section nhỏ như setup, models) |

---

## 4. My Approach — Cá nhân (10 điểm)

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `r'(?<=[.!?])\s+'` để split text theo ranh giới câu. Các câu được nhóm lại theo `max_sentences_per_chunk` bằng list slicing rồi join bằng space.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử separator theo thứ tự ưu tiên: `\n\n` → `\n` → `. ` → ` ` → `""`. Base case: nếu `len(text) <= chunk_size` thì trả nguyên.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Lưu trữ in-memory dưới dạng list các dict. Hàm `search` sử dụng cosine similarity (thông qua dot product do vector đã được normalized hoặc mock) để tìm top_k.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter`: Lọc metadata trước khi tính toán độ tương đồng. `delete_document`: Xóa các bản ghi có `doc_id` tương ứng.

### KnowledgeBaseAgent

**`answer`** — approach:
> Thực hiện quy trình RAG: Tìm kiếm các chunk liên quan nhất, gộp lại làm context, và đưa vào prompt để LLM trả lời.

### Test Results

```
============================= test session starts =============================

...tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                 [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                          [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                   [  7%] 
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                    [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                         [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                         [ 14%] 
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                               [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                              [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                           [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                       [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                 [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                        [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                            [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                      [ 40%] 
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                            [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                  [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                    [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                          [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                               [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                 [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                     [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                  [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                           [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                          [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                     [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                 [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                            [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                      [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED             [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                           [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                          [ 88%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED              [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                         [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                  [ 95%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED        [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED            [100%] 

============================== 42 passed in 0.77s =============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Mục tiêu của Lab Ngày 7 là tìm hiểu về Vector Store" | "Học cách triển khai RAG pattern trong Lab 7" | Cao | -0.0398 | Sai |
| 2 | "Cách cài đặt Local Embedder" | "Sử dụng sentence-transformers để chạy embedding" | Cao | -0.0909 | Sai |
| 3 | "RecursiveChunker chia nhỏ văn bản đệ quy" | "Chiến lược chunking dựa trên câu" | Trung bình | -0.0355 | Đúng |
| 4 | "Hệ thống RAG giúp chatbot tra cứu tài liệu" | "Thời tiết hôm nay có nắng nhẹ" | Thấp | -0.0926 | Đúng |
| 5 | "Nộp bài vào thư mục report" | "Hoàn thành các TODO trong src package" | Trung bình | 0.1969 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là các cặp câu mang tính kỹ thuật rất gần nhau (Pair 1, 2) nhưng score lại rất thấp hoặc âm. Điều này khẳng định `MockEmbedder` (sử dụng random/hash) không thể xử lý ngữ nghĩa thực sự.

---

## 6. Results — Cá nhân (10 điểm)

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Cách tính điểm cho bài tập UX Ngày 5 là gì? | Dựa trên tiêu chí trải nghiệm người dùng và tính khả thi (chi tiết trong day05.md). |
| 2 | Các giai đoạn chính của Lab Ngày 7 gồm những gì? | Gồm 2 Phase: Cá nhân (implement src) và Nhóm (benchmark strategy). |
| 3 | Deadline nộp SPEC draft là lúc mấy giờ? | Thường được quy định vào cuối ngày hoặc theo timeline trong day05.md. |
| 4 | Sự khác biệt giữa Mock prototype và Working prototype là gì? | Mock là bản mô phỏng giao diện, Working là bản có chức năng thực tế (day06.md). |
| 5 | Cấu trúc thư mục của Phase 3 yêu cầu gì? | Yêu cầu các folder src, tests và notebook rõ ràng (day03.md). |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Cách tính điểm cho bài tập UX Ngày 5 là gì? | # Ngày 5 — Thiết kế sản phẩm AI cho sự không chắc chắn... | 0.0469 | Đúng | [MOCK LLM] Dựa trên tài liệu Lab: "# Ngày 5 — Thiế... |
| 2 | Các giai đoạn chính của Lab Ngày 7 gồm những gì? | # Lab 3: Chatbot vs ReAct Agent (Industry Edition) | -0.0387 | Sai | [MOCK LLM] Dựa trên tài liệu Lab: "# Lab 3: Chatbo... |
| 3 | Deadline nộp SPEC draft là lúc mấy giờ? | # Ngày 6 — Hackathon: SPEC → Prototype → Demo... | 0.1817 | Đúng | [MOCK LLM] Dựa trên tài liệu Lab: "# Ngày 6 — Hack... |
| 4 | Sự khác biệt giữa Mock prototype và Working prototype là gì? | # Ngày 2 — Tìm Đúng Bài Toán — Updated for v2 Metrics... | 0.1667 | Đúng | [MOCK LLM] Dựa trên tài liệu Lab: "# Ngày 2 — Tìm ... |
| 5 | Cấu trúc thư mục của Phase 3 yêu cầu gì? | ### 3. Directory Structure\n- `src/tools/`: Extension... | 0.0293 | Đúng | [MOCK LLM] Dựa trên tài liệu Lab: "### 3. Directo... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> điều hay nhất tôi học được là xử lý vấn đề tốt 

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> cách họ xử lý các file văn bản tiếng Việt có dấu và tối ưu hóa chunking cho code snippets.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> flex nhiều model embedder để có thể so sánh và chọn ra nhiều model tốt nhất 

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **100 / 100** |
