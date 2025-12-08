# 🚀 ShopSight - Quick Start Guide

## Installation Steps

### 1. Install Node.js (if not already installed)

Download from: **https://nodejs.org/**
- Choose the **LTS (Long Term Support)** version
- Run the installer
- Restart PowerShell after installation

### 2. Install Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

### 3. Set Up Gemini API Key (Recommended)

1. Go to: https://aistudio.google.com/app/apikey
2. Create an API key
3. Edit `.env` file in project root:
   ```
   GEMINI_API_KEY=your-key-here
   ```

> **Note:** App works without API key using keyword fallback, but with limited NLP capabilities.

## Running the Application

### Terminal 1: Start Backend

```powershell
python backend\app.py
```

You should see:
```
Loading product data...
Loading customer data (sample)...
Loaded 105542 products and 100 customers

============================================================
  ShopSight API Server
============================================================
  Server running at: http://localhost:5000
  Frontend URL: http://localhost:3000
  Debug mode: True
============================================================
```

### Terminal 2: Start Frontend

```powershell
cd frontend
npm start
```

Browser will automatically open to `http://localhost:3000`

## Testing the App

### 1. Try These Searches:

- "black shoes"
- "red dress"
- "running gear"
- "women's jacket"
- "blue jeans"

### 2. Click Any Product

You'll see:
- ✅ Sales history chart (12 months)
- ✅ 3-month forecast with confidence intervals
- ✅ Customer segment breakdown
- ✅ Buyer personas
- ✅ AI-generated insights

## Troubleshooting

### Backend won't start?

```powershell
# Ensure virtual environment is activated
kumo\Scripts\activate

# Verify dependencies
pip install -r requirements.txt
```

### Frontend won't start?

```powershell
# Verify Node.js is installed
node --version
npm --version

# Reinstall dependencies
cd frontend
rm -r node_modules
npm install
```

### "LLM API error"?

- Check your GEMINI_API_KEY is correct in `.env`
- Verify the API key is active at https://aistudio.google.com
- App still works without it (uses fallback mode)

### "No products found"?

- Verify backend is running on port 5000
- Check browser console for errors (F12)
- Try a simpler query like "shoes"

## Next Steps

- Read the full [README.md](../README.md) for detailed documentation
- Explore the backend API at `http://localhost:5000/api/search?query=shoes`
- Check out the code in `backend/` and `frontend/src/`
- Take screenshots for your demo!

---

**Need Help?** Check the main README or create an issue on GitHub.
