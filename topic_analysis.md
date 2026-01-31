# Chat Assistant with Session Memory – Technical Report

## 0. Tổng quan dự án

### Mục tiêu

Xây dựng một **chat assistant backend** có khả năng:

* Ghi nhớ **ngắn hạn (session memory)** thông qua **tóm tắt tự động**
* Hiểu và tinh chỉnh truy vấn người dùng (**query understanding & refinement**)
* Xuất output **có cấu trúc (structured JSON)**, ổn định, dễ kiểm thử

### Pipeline tổng thể

```
User Input
   ↓
Session Context Manager
   ↓
Session Summarization (nếu vượt ngưỡng)
   ↓
Query Understanding Pipeline
   ↓
Final Prompt Construction
   ↓
LLM Response
```

---

## 1. Session Memory via Summarization

### Chức năng

Tự động **tóm tắt phiên hội thoại** khi tổng context vượt quá ngưỡng cho phép (ví dụ: 10k tokens), nhằm:

* Giảm chi phí và độ trễ
* Giữ lại thông tin quan trọng
* Hỗ trợ truy vấn về sau

---

### 🔹 (1) Theo dõi kích thước context

**Ý nghĩa**

* Hệ thống cần biết **khi nào context quá dài**
* Có thể dùng:

  * Heuristic đơn giản (đếm ký tự / từ)
  * Hoặc tokenizer-based (tốt hơn)

**Ví dụ input**

```text
Conversation length = 12,400 tokens
Configured threshold = 10,000 tokens
```

**Phân tích**

* Context đã vượt ngưỡng → cần trigger summarization

---

### 🔹 (2) Kích hoạt session summarization

**Ý nghĩa**

* Lấy một dải message cũ để tóm tắt
* Không tóm tắt toàn bộ, chỉ phần đã “ổn định”

**Ví dụ**

* Tóm tắt message từ index 0 → 42
* Giữ lại message gần nhất cho hội thoại tiếp

---

### 🔹 (3) Sinh session summary có cấu trúc

**Ý nghĩa**

* Summary **không phải text tự do**
* Phải theo **schema rõ ràng** để máy xử lý tiếp

**Ví dụ output JSON (schema mẫu)**

```json
{
  "session_summary": {
    "user_profile": {
      "prefs": ["thích dùng Python", "ưu tiên demo CLI"],
      "constraints": ["không dùng framework nặng"]
    },
    "key_facts": [
      "Dự án là Chat Assistant with Session Memory",
      "Python là ngôn ngữ bắt buộc"
    ],
    "decisions": [
      "Dùng heuristic token counting"
    ],
    "open_questions": [
      "Có cần tích hợp vector database không?"
    ],
    "todos": [
      "Viết README.md",
      "Chuẩn bị test data JSONL"
    ]
  },
  "message_range_summarized": {
    "from": 0,
    "to": 42
  }
}
```

---

### 🔹 (4) Lưu session memory

**Ý nghĩa**

* Session summary được lưu lại để:

  * Augment context
  * Hiểu truy vấn sau này

**Cách lưu**

* File system (JSON)
* SQLite / NoSQL DB

---

## 2. Query Understanding and Refinement

### Chức năng

Khi nhận query mới, hệ thống phải:

1. Phát hiện mơ hồ
2. Viết lại câu hỏi nếu cần
3. Bổ sung ngữ cảnh từ session memory
4. Sinh câu hỏi làm rõ (nếu vẫn chưa đủ)

---

## 2.1 Step 1 — Rewrite / Paraphrase (Ambiguity Detection)

### 🔹 (1) Phát hiện câu hỏi mơ hồ

**Ý nghĩa**

* Nhận diện các dấu hiệu:

  * Đại từ không rõ: *nó, cái đó, cái này*
  * Thiếu đối tượng, thiếu mục tiêu

**Ví dụ**

```
User: "làm cái đó sao?"
```

**Phân tích**

* ❌ Mơ hồ:

  * “cái đó” là gì?
  * Là code? session memory? demo?

---

### 🔹 (2) Viết lại truy vấn rõ nghĩa hơn

**Ý nghĩa**

* Dựa vào **session memory**
* Viết lại query có chủ ngữ, hành động, đối tượng rõ ràng

**Ví dụ output JSON**

```json
{
  "original_query": "làm cái đó sao?",
  "is_ambiguous": true,
  "rewritten_query": "Làm thế nào để triển khai session memory bằng cơ chế summarization cho chatbot?"
}
```

---

### 🔹 (3) Trường hợp không mơ hồ

**Ví dụ**

```
User: "Khi nào thì trigger session summarization?"
```

**Phân tích**

* ✅ Rõ ràng
* Không cần rewrite

```json
{
  "original_query": "Khi nào thì trigger session summarization?",
  "is_ambiguous": false,
  "rewritten_query": null
}
```

---

## 2.2 Step 2 — Context Augmentation

### 🔹 (1) Xác định context cần lấy

**Ý nghĩa**

* Không đưa toàn bộ memory
* Chỉ lấy **trường liên quan**

**Ví dụ**

* Query liên quan đến thiết kế → cần:

  * `key_facts`
  * `decisions`

---

### 🔹 (2) Kết hợp context

**Nguồn context**

* N message gần nhất
* Relevant session memory fields

**Ví dụ output JSON**

```json
{
  "needed_context_from_memory": [
    "key_facts",
    "decisions"
  ],
  "final_augmented_context": "Project: Chat Assistant with Session Memory. Decision: use heuristic token counting. User prefers Python CLI demo."
}
```

---

## 2.3 Step 3 — Clarifying Questions

### 🔹 (1) Phát hiện vẫn chưa rõ sau rewrite

**Ví dụ**

```
User: "tối ưu nó thêm được không?"
```

**Phân tích**

* Không rõ:

  * “nó” là pipeline?
  * tối ưu hiệu năng hay accuracy?

---

### 🔹 (2) Sinh câu hỏi làm rõ

**Nguyên tắc**

* 1–3 câu
* Ngắn gọn
* Trực tiếp vào điểm chưa rõ

**Ví dụ output JSON**

```json
{
  "original_query": "tối ưu nó thêm được không?",
  "is_ambiguous": true,
  "rewritten_query": "Có thể tối ưu pipeline chat assistant không?",
  "needed_context_from_memory": ["key_facts"],
  "clarifying_questions": [
    "Bạn muốn tối ưu hiệu năng hay chất lượng trả lời?",
    "Phần nào của pipeline bạn quan tâm nhất?"
  ],
  "final_augmented_context": "User is building a Chat Assistant with Session Memory using Python."
}
```

---

## 3. Demo Flows

### 3.1 Flow 1 — Session Memory Trigger

**Demo yêu cầu**

* Load conversation dài
* In log context size
* Trigger summarization
* In session summary JSON

**Ví dụ log**

```
Context size: 9,800 tokens
Context size: 10,200 tokens → Trigger summarization
```

---

### 3.2 Flow 2 — Ambiguous Query Handling

**Demo yêu cầu**

* Input mơ hồ
* Hiển thị:

  * Rewrite
  * Context augmentation
  * Clarifying questions

---

## 4. Structured Output & Schema-first Design

### Lý do dùng schema

* Dễ validate
* Dễ test
* Dễ mở rộng agent / tool calling

**Hai schema chính**

1. `SessionSummarySchema`
2. `QueryUnderstandingSchema`

---

