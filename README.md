# Chat Assistant Backend with Session Memory

Dự án này là một bản demo kỹ thuật (Technical Demo) xây dựng backend cho một Chat Assistant thông minh. Hệ thống tập trung vào hai tính năng cốt lõi: **Session Memory (Bộ nhớ ngắn hạn qua tóm tắt tự động)** và **Query Understanding Pipeline (Đường ống xử lý và làm rõ ý định người dùng)**.

Hệ thống được thiết kế theo kiến trúc tách biệt Client-Server, sử dụng mô hình **Llama-3-8B-Instruct** và tuân thủ chặt chẽ việc kiểm soát đầu ra bằng **Structured Outputs (Pydantic Schema)**.

<p align="center">
  <img src="/imgs/flow.png" alt="Pipeline Flow" width="100%"/>
</p>


---

## 🛠️ Yêu cầu hệ thống

Hệ thống hoạt động theo mô hình Client-Server:

1. **Server (Backend Model):** Chạy trên môi trường có GPU (Google Colab A100) để host Llama-3 qua FastAPI.
2. **Client (Application):** Chạy trên máy cá nhân (Localhost), sử dụng Python 3.11 và Streamlit.

---

## 🚀 Hướng dẫn Cài đặt & Thiết lập

### 1. Chuẩn bị Server (Google Colab)

Mô hình Llama-3-8B yêu cầu GPU — thường chạy trên Google Colab và được expose bằng `ngrok`. Nếu bạn có template Colab, dùng nó; nếu không, bạn có hai lựa chọn:

- Chạy một server LLM có sẵn và đặt `LLM_API_BASE_URL` tới endpoint đó.

Nếu bạn sử dụng Colab, những bước chính là:

1. Tạo Notebook mới trên Colab và chọn Runtime → GPU (A100 nếu có).
2. Thêm các biến/secret cần thiết vào notebook (ví dụ `HF_TOKEN`, `NGROK_TOKEN`) và khởi chạy server.

> Hoặc dùng API của bạn (xem `Config.LLM_API_BASE_URL`) — Streamlit client sẽ kết nối tới URL đó.

5. Chạy cell. Khi server khởi động thành công, bạn sẽ nhận được một URL dạng:

```text
🚀 API BASE URL: https://xxxx-xx-xx-xx-xx.ngrok-free.app/v1

```

_Lưu lại URL này để cấu hình ở bước sau._

### 2. Cài đặt Client (Local Machine)

**Bước 1: Clone dự án và tạo môi trường ảo**
Khuyến nghị sử dụng **Python 3.11**.

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường (Windows)
venv\Scripts\activate

# Kích hoạt môi trường (Mac/Linux)
source venv/bin/activate

```

**Bước 2: Cài đặt thư viện**

```bash
pip install -r requirements.txt

```

**Bước 3: Cấu hình biến môi trường**
Tạo file `.env` tại thư mục gốc.

Ví dụ tối thiểu của `.env` (thay `...` bằng giá trị thực):

```ini
LLM_API_BASE_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app/v1
MEMORY_THRESHOLD_TOKENS=200
```



---

## 🏃‍♂️ Cách chạy Demo

Sau khi server Colab đã chạy và file `.env` đã được cấu hình, bạn khởi động giao diện Streamlit bằng lệnh:

```bash
streamlit run demo/streamlit_app.py

```

Ứng dụng sẽ tự động mở tại `http://localhost:8501`.

---

## 🧪 Các bước kiểm thử (Testing Flows)

Dự án đi kèm với dữ liệu test trong thư mục `tests/test_data/` để kiểm chứng các tính năng cốt lõi.

### Flow 1: Kiểm thử Session Memory (Tự động tóm tắt)

**Mục tiêu:** Chứng minh hệ thống tự động tóm tắt hội thoại khi vượt quá giới hạn token.

1. Trên giao diện Streamlit, nhìn vào Sidebar bên trái.
2. Điều chỉnh thanh trượt **Memory Threshold** xuống thấp (ví dụ: `200` tokens).
3. Nhấn nút **"Load Long Conversation (Trigger Memory)"**.
4. **Kết quả mong đợi:**

- Hệ thống tải đoạn hội thoại dài từ file `tests/test_data/long_conversation.jsonl`.
- Token counter (hiển thị trong tab "Pipeline Visualizer" hoặc Log) sẽ vượt ngưỡng.
- Một thông báo "Summarization Triggered!" xuất hiện.
- Chuyển sang tab **"💾 Memory & State"**, bạn sẽ thấy JSON tóm tắt (UserProfile, Key Facts, v.v.).

### Flow 2: Kiểm thử Query Understanding (Xử lý câu hỏi mơ hồ)

**Mục tiêu:** Chứng minh hệ thống phát hiện câu hỏi không rõ ràng và tự động viết lại.

1. Mở file `tests/test_data/test_queries.md` để xem ví dụ, hoặc nhập trực tiếp vào khung chat.
2. Mở tab **"🛠️ Pipeline Visualizer"** (hoặc xem log ngay trên khung chat).
3. **Kết quả mong đợi:**

- Step "Query Analysis" hiển thị JSON.
- `is_ambiguous`: `true`.
- Hệ thống trả lời dựa trên câu hỏi đã được viết lại.

---

## 📂 Giải thích Cấu trúc Dự án

Dự án được tổ chức theo cấu trúc module hóa, tách biệt rõ ràng giữa logic nghiệp vụ (Business Logic) và giao diện (UI).

```text
chat-assistant-backend/
├── src/                        # SOURCE CODE CHÍNH
│   ├── __init__.py
│   ├── config.py               # Quản lý cấu hình (Load biến môi trường, đường dẫn file).
│   ├── models.py               # Pydantic Schemas. Định nghĩa cấu trúc dữ liệu input/output (Validation).
│   ├── session_memory.py       # CORE FEATURE A. Logic quản lý bộ nhớ và kích hoạt tóm tắt (Summarization).
│   ├── query_processor.py      # CORE FEATURE B. Pipeline xử lý câu hỏi: Ambiguity check -> Rewrite -> Augment.
│   ├── token_counter.py        # Tiện ích đếm token (sử dụng tiktoken).
│   ├── llm_client.py           # Client giao tiếp với API Server (Llama-3). Xử lý request/response.
│   └── storage.py              # Quản lý File I/O (Lưu/Đọc session memory và test data).
│
├── demo/
│   └── streamlit_app.py        # Giao diện người dùng (UI). Kết nối các module trong /src để demo flow.
│
├── data/
│   └── sessions/               # Thư mục chứa file bộ nhớ phiên làm việc (được tạo ra khi chạy runtime).
│
├── tests/
│   └── test_data/              # Dữ liệu giả lập để kiểm thử nhanh.
│       ├── long_conversation.jsonl  # Hội thoại dài để test tính năng Memory Trigger.
│       └── test_queries.md           # Ví dụ câu hỏi (mơ hồ / rõ ràng) để test pipeline.
│
├── requirements.txt            # Danh sách thư viện Python cần thiết.
├── run_server.py               # (placeholder) local server script — không kèm Colab template.
└── README.md                   # Tài liệu hướng dẫn sử dụng (File này).
└── colab_server.ipynb          # Host model LLM (Llama-3)



```

### Chi tiết các module quan trọng trong `src/`:

- **`models.py`**: Đây là "xương sống" của việc structured output. Thay vì để LLM trả về chuỗi tự do, file này định nghĩa các class như `SessionMemory`, `QueryAnalysis` giúp ép kiểu dữ liệu trả về thành JSON chuẩn xác.
- **`session_memory.py`**: Chứa hàm `check_and_summarize`. Hàm này kiểm tra số lượng token hiện tại so với `MEMORY_THRESHOLD_TOKENS`. Nếu vượt quá, nó gọi LLM để tóm tắt hội thoại cũ thành cấu trúc JSON và lưu lại.
- **`query_processor.py`**: Thực hiện chuỗi xử lý:

1. Nhận câu hỏi người dùng.
2. Kết hợp với ngữ cảnh hội thoại gần nhất và bộ nhớ session.
3. Hỏi LLM: "Câu này có mơ hồ không? Nếu có hãy viết lại".
4. Trả về đối tượng `QueryAnalysis` chứa câu hỏi đã được làm rõ.

---

## ⚠️ Lưu ý & Giới hạn

1. **Tốc độ:** Do sử dụng mô hình Llama-3-8B qua ngrok (tunneling), độ trễ (latency) có thể cao hơn so với gọi API thương mại trực tiếp (như OpenAI).
2. **Context Window:** Demo sử dụng giới hạn context token an toàn (~2048 - 4096 tokens) để đảm bảo độ ổn định trên Colab.
3. **Dữ liệu:** Dữ liệu session được lưu dưới dạng file JSON cục bộ trong thư mục `data/sessions/` để đơn giản hóa việc triển khai (không setup Database riêng).
