# ReviewMind — AI-Powered Systematic Literature Review Automation Tool

FastAPI backend (multi-agent pipeline) + React (Vite) PWA frontend, with Bengali/English language support.

## ✅ সব ফিচার (v2 — multi-agent + ML)

1. **Search Agent** — Semantic Scholar API থেকে পেপার সার্চ
2. **Dedup Agent (ML)** — sentence-transformers embedding + cosine similarity দিয়ে ডুপ্লিকেট বাদ
3. **Screening Agent** — Gemini দিয়ে Include/Exclude, কারণ ও confidence সহ
4. **Quality-Check Agent** — Screening Agent এর ডিসিশন আবার যাচাই করে (agree/override)
5. **Extraction Agent** — methodology, sample size, findings, limitations টেবিলে
6. **Coordinator Agent** — উপরের সব agent-কে চেইন করে একটা `/api/pipeline` কলে চালায়
7. **PRISMA diagram + Word report** — এক ক্লিকে ডাউনলোড
8. **Paper Q&A Chat** — যেকোনো পেপারের abstract নিয়ে প্রশ্ন করা যায়
9. **Quiz Generator** — একাডেমিক MCQ কুইজ অটো জেনারেট
10. **Language selector (EN/বাংলা)** — UI + AI আউটপুট দুটোই ভাষা টগল করে
11. **Landing page** — hero, how-it-works, feature cards
12. **PWA** — ইনস্টলযোগ্য

## চালানোর নির্দেশনা

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env ফাইলে GEMINI_API_KEY বসাও (ফ্রি: https://aistudio.google.com/apikey)
uvicorn app.main:app --reload --port 8000
```
প্রথমবার চালানোর সময় sentence-transformers মডেল (all-MiniLM-L6-v2, ~80MB) অটো ডাউনলোড হবে — ইন্টারনেট লাগবে।

### Frontend
```bash
cd frontend
npm install
npm run dev
```
http://localhost:5173

## নতুন এন্ডপয়েন্ট

- `POST /api/pipeline` — { keyword, criteria, lang } → পুরো multi-agent পাইপলাইন চালায়
- `POST /api/chat` — { context_text, question, lang } → পেপার নিয়ে প্রশ্নের উত্তর
- `POST /api/quiz` — { context_text, num_questions, lang } → MCQ কুইজ

## Workflow

1. ল্যান্ডিং পেজে ভাষা সিলেক্ট করে Get Started
2. টপিক ও criteria দিয়ে "Run full pipeline" — Search→Dedup→Screen→QualityCheck→Extract সব অটো
3. টেবিলে যেকোনো পেপারে ক্লিক করলে Chat ও Quiz প্যানেল খুলবে
4. Download Report চাপলে PRISMA diagram + Word রিপোর্ট

## Deploy (ফ্রি টিয়ার)
Backend → Render/Railway, Frontend → Vercel/Netlify। Deploy-এর পর `frontend/src/api.js`-এ `API_BASE` আপডেট করো।
