# 🧠 AI Mindmap Generator

Tự động tạo mindmap từ PDF bằng thuật toán NLP — không dùng ChatGPT/Gemini.

## 🚀 Chạy local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000

## 🌐 Deploy

- **Frontend**: Vercel — import repo, set `NEXT_PUBLIC_API_URL`
- **Backend**: Render — connect repo, chọn thư mục `backend/`

## ⚙️ Stack

- Backend: FastAPI · PyMuPDF · underthesea · scikit-learn · networkx
- Frontend: Next.js · React Flow · TailwindCSS
- DB: SQLite
