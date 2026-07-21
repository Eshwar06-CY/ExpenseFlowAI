# Contributing to ExpenseFlow AI

Thank you for contributing to ExpenseFlow AI! Follow these guidelines to set up your environment and submit clean changes.

---

## 💻 Local Development Setup

### Backend Setup
1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Initialize virtual environment and activate:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations and start dev server:
   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to frontend:
   ```bash
   cd frontend
   ```
2. Install npm node modules:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```

---

## 🧪 Testing Guidelines

Before opening a pull request, run all integration checks locally to ensure no regressions:
```bash
# Run backend test suite
python backend/tests/test_production.py

# Verify frontend build compiles successfully
npm --prefix frontend run build
```

---

## 🎨 Code Style Rules

- **Python**: Follow standard PEP 8 naming. Write type hints for new functions and API routes. Use SQLAlchemy 2.0 select queries rather than legacy query syntax.
- **React**: Use functional hooks. Never use raw window alerts or confirmation prompts; import custom components (`useToast`, `ConfirmDialog`) instead. Keep bundle sizes clean through lazy-loaded pages.
