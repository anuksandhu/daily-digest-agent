# Setup and Deployment Guide

## Complete Setup Instructions

This guide will help you set up and deploy the Daily Digest application from scratch.

---

## Part 1: Local Development Setup

### Step 1: Prerequisites

Ensure you have:
- Python 3.11 or higher
- pip (Python package manager)
- Git
- Text editor (VS Code recommended)

Check Python version:
```bash
python --version
# Should show Python 3.11.x or higher
```

### Step 2: Get API Keys

#### Required API Keys

**1. Google Gemini API** (Required)
- Go to: https://aistudio.google.com/app/apikey
- Click "Create API Key"
- Copy the key (starts with "AIza...")
- Save it securely

**2. OpenWeather API** (Required)
- Go to: https://openweathermap.org/api
- Sign up for free account
- Navigate to "API keys" tab
- Copy your API key
- Save it securely

#### Optional API Keys (for enhanced features)

**3. Brave Search API** (Optional - for web search via MCP)
- Go to: https://brave.com/search/api/
- Sign up and get API key

**4. News API** (Optional - for real tech news)
- Go to: https://newsapi.org/
- Sign up for free tier (100 requests/day)
- Get your API key

**5. Alpha Vantage** (Optional - for real market data)
- Go to: https://www.alphavantage.co/
- Sign up for free tier (500 requests/day)
- Get your API key

### Step 3: Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/daily-digest.git
cd daily-digest

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API keys
# Use any text editor (e.g., nano, vim, VS Code)
nano .env
```

In the `.env` file, set at minimum:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
OPENWEATHER_API_KEY=your_actual_openweather_key_here
```

### Step 5: Test Local Generation

```bash
# Generate digest
cd src
python generate_digest.py

# You should see output like:
# ======================================================================
# Starting Daily Digest Generation
# ======================================================================
# Using model: gemini-2.5-flash-lite
# ...
# Daily Digest Generation Complete!
```

### Step 6: View Results

```bash
# Open the generated HTML in your browser
# On Mac:
open ../docs/index.html
# On Linux:
xdg-open ../docs/index.html
# On Windows:
start ../docs/index.html

# Or manually navigate to daily-digest/docs/index.html
```

You should see a beautiful dashboard with weather, sports, tech news, and market data!

---

## Part 2: GitHub Deployment

### Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `daily-digest`
3. Description: "Automated daily digest using Google ADK agents"
4. Set to **Public** (required for free GitHub Pages)
5. **Do NOT** initialize with README (we already have one)
6. Click "Create repository"

### Step 2: Push Code to GitHub

```bash
# Make sure you're in the project root directory
cd /path/to/daily-digest

# Initialize git (if not already done)
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: Daily Digest agent system"

# Add remote origin (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/daily-digest.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

Add these secrets one by one:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `GOOGLE_API_KEY` | Your Gemini API key | ✅ Yes |
| `OPENWEATHER_API_KEY` | Your OpenWeather key | ✅ Yes |
| `BRAVE_API_KEY` | Your Brave Search key | ⚪ Optional |
| `NEWS_API_KEY` | Your News API key | ⚪ Optional |
| `FINANCE_API_KEY` | Your Alpha Vantage key | ⚪ Optional |

For each secret:
- Click "New repository secret"
- Name: Enter the secret name (e.g., `GOOGLE_API_KEY`)
- Value: Paste your API key
- Click "Add secret"

### Step 4: Enable GitHub Pages

1. Go to repository **Settings**
2. Scroll down to **Pages** section (left sidebar)
3. Under "Source", select:
   - Branch: `main`
   - Folder: `/docs`
4. Click **Save**
5. Wait 1-2 minutes for deployment
6. Your site will be available at: `https://YOUR_USERNAME.github.io/daily-digest`

### Step 5: Run First Workflow

1. Go to **Actions** tab in your repository
2. You should see "Generate Daily Digest" workflow
3. Click on the workflow name
4. Click **Run workflow** dropdown (right side)
5. Select branch: `main`
6. Click **Run workflow** button
7. Wait ~30-60 seconds
8. Click on the workflow run to see logs
9. Once complete (green checkmark), visit your site!

### Step 6: Verify Deployment

1. Go to: `https://YOUR_USERNAME.github.io/daily-digest`
2. You should see your generated digest
3. Check that all sections are present:
   - 🌤️ Weather
   - 🏈 Sports  
   - 💻 Tech News
   - 📈 Markets
4. Verify the "Last updated" timestamp is recent

---

## Part 3: Scheduled Updates

### Automatic Daily Updates

The workflow is already configured to run automatically every day at 8:00 AM PST (16:00 UTC).

You can verify the schedule:
1. Go to repository
2. Open `.github/workflows/daily-digest.yml`
3. Look for the `schedule` section:
```yaml
schedule:
  - cron: '0 16 * * *'  # 8:00 AM PST
```

### Change Schedule (Optional)

To run at a different time, edit the cron expression:

- 6:00 AM PST: `0 14 * * *`
- 12:00 PM PST: `0 20 * * *`
- 6:00 PM PST: `0 2 * * *`

Cron format: `minute hour day month weekday`
- Use: https://crontab.guru/ to help create schedules

### Manual Trigger Anytime

You can manually trigger the workflow anytime:
1. Go to **Actions** tab
2. Click "Generate Daily Digest"
3. Click **Run workflow**
4. Wait ~30 seconds
5. Check your site for updates

---

## Part 4: Customization

### Change Location

Edit `src/utils/config.py`:
```python
default_location: str = "New York, NY"  # Change this
```

Or set environment variable:
```
DEFAULT_LOCATION=London, UK
```

### Change Teams

Edit `src/utils/config.py`:
```python
sports_teams: dict = {
    "nfl": "Patriots",    # Change team names
    "nhl": "Bruins",
    "nba": "Celtics"
}
```

### Change Tech Topics

Edit `src/utils/config.py`:
```python
tech_topics: list = ["blockchain", "web3", "crypto"]  # Your interests
```

### Change Market Indexes

Edit `src/utils/config.py`:
```python
market_indexes: list = ["^FTSE", "^N225", "^HSI"]  # Other indexes
```

After any customization:
```bash
git add .
git commit -m "Customize configuration"
git push origin main
```

Then manually trigger the workflow to see your changes.

---

## Part 5: Monitoring and Debugging

### View Logs

**Local logs:**
```bash
cat logs/digest-YYYYMMDD.log
```

**GitHub Actions logs:**
1. Go to **Actions** tab
2. Click on a workflow run
3. Click on "generate" job
4. Expand steps to see detailed logs

### View Metrics

Check `docs/metrics.json` for performance data:
```bash
cat docs/metrics.json
```

Or view in browser at:
`https://YOUR_USERNAME.github.io/daily-digest/metrics.json`

### Troubleshooting

**Problem: "GOOGLE_API_KEY not found"**
- Solution: Add API key to GitHub Secrets or local .env file

**Problem: "Weather data failed"**
- Solution: Check OpenWeather API key is valid and has quota remaining

**Problem: Workflow fails silently**
- Solution: Check Actions tab for error logs, verify all secrets are set

**Problem: GitHub Pages not updating**
- Solution: Ensure Pages is set to deploy from `/docs` folder on `main` branch

**Problem: Mock data showing instead of real data**
- Solution: Add optional API keys (NEWS_API_KEY, FINANCE_API_KEY, etc.)

---

## Part 6: Submission Checklist

Before submitting your project, ensure:

- [ ] ✅ Repository is public
- [ ] ✅ README.md is complete with your GitHub username
- [ ] ✅ ARCHITECTURE.md is present
- [ ] ✅ PROJECT_WRITEUP.md is complete (<1500 words)
- [ ] ✅ Code has comments explaining implementation
- [ ] ✅ GitHub Actions workflow runs successfully
- [ ] ✅ GitHub Pages is deployed and accessible
- [ ] ✅ All API keys are in GitHub Secrets (never in code!)
- [ ] ✅ Site shows current, factual data
- [ ] ✅ Logs and metrics are being generated
- [ ] ✅ At least 3 agent concepts demonstrated (you have 7!)

---

## Part 7: Submission Package

Your submission should include:

**1. GitHub Repository Link**
- URL: `https://github.com/YOUR_USERNAME/daily-digest`
- Must be public

**2. Live Demo Link**
- URL: `https://YOUR_USERNAME.github.io/daily-digest`
- Should show recent digest

**3. Project Writeup**
- File: `PROJECT_WRITEUP.md`
- Word count: <1500 words
- Covers: Problem, Solution, Architecture, Results

**4. Documentation**
- `README.md` - Setup instructions and overview
- `ARCHITECTURE.md` - Detailed technical architecture
- Code comments throughout

**5. Evidence of 3+ Agent Concepts**
- Multi-agent system ✅
- Custom tools ✅
- Sessions ✅
- Observability ✅
- Metrics ✅
- Validation ✅
- (7 total - exceeds requirement!)

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in `logs/` directory
3. Check GitHub Actions workflow logs
4. Verify all API keys are correct
5. Ensure Python 3.11+ is installed

For more help:
- Review ARCHITECTURE.md for technical details
- Check README.md for feature documentation
- Review Google ADK docs: https://google.github.io/adk-docs/

---

**Congratulations! Your Daily Digest agent system is now production-ready!** 🎉
