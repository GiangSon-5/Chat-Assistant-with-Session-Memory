### Trường hợp 1: Câu hỏi rõ ràng – Không cần làm rõ

**`is_ambiguous = false`, `requires_clarification = false`**

* **Mô tả:**
  Câu hỏi đầy đủ thông tin, rõ ràng về ý định và nội dung. AI có thể xử lý và trả lời ngay.

* **Ví dụ input:**

  > *How do I implement structured JSON output using Llama 3 and FastAPI?*

* **Kỳ vọng hệ thống:**

  * Không đánh dấu mơ hồ
  * Không yêu cầu làm rõ
  * Giữ nguyên câu hỏi gốc

* **Hành vi UI:**
  AI xử lý và trả lời trực tiếp.

---

### Trường hợp 2: Câu hỏi mơ hồ về ngữ nghĩa

**`is_ambiguous = true`, `requires_clarification = true`**

* **Mô tả:**
  Câu hỏi sử dụng đại từ hoặc tham chiếu không rõ ràng (ví dụ: *it, this, that*), không đủ thông tin để suy luận từ ngữ cảnh.

* **Ví dụ input:**

  > *Why is it so slow?*
  > **Why is the Llama 3 model responding so slowly when I call it through FastAPI?**

* **Vấn đề:**
  Không rõ “it” đang nói đến thành phần nào (model, API, hệ thống…).

* **Kỳ vọng hệ thống:**

  * Đánh dấu câu hỏi mơ hồ
  * Chỉ ra lý do mơ hồ
  * Sinh câu hỏi làm rõ phù hợp

* **Hành vi UI:**
  AI dừng xử lý và yêu cầu người dùng làm rõ ý định.

---


## Mẹo tạo test nhanh cho từng trường hợp

* **Muốn câu hỏi rõ ràng:**
  Sử dụng danh từ cụ thể (FastAPI, PostgreSQL, Llama 3, AWS).

* **Muốn tạo câu hỏi mơ hồ:**
  Dùng đại từ hoặc tham chiếu chung chung (*it, this, that, the other option*).

* **Muốn kiểm tra yêu cầu làm rõ:**
  Ra lệnh hành động (viết code, deploy, config) nhưng không chỉ rõ đối tượng hoặc tham số.

