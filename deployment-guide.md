# Deploying RAG Agent on Render.com with Docker

## 📁 Project Structure
```
rag-agent/
├── app.py                    # Main Streamlit application
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── .dockerignore            # Files to exclude from Docker
├── render.yaml              # Render deployment config
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── README.md                # This file
```

## 🚀 Deployment Steps

### 1. Prepare Your Repository

1. Create a new GitHub repository
2. Add all the files from this project:
   - `app.py`
   - `Dockerfile`
   - `requirements.txt`
   - `.dockerignore`
   - `render.yaml`
   - `.streamlit/config.toml`

3. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial commit: RAG Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rag-agent.git
git push -u origin main
```

### 2. Set Up Render.com

1. **Sign up/Login** to [Render.com](https://render.com)

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your RAG agent

3. **Configure the Service:**
   - **Name:** `rag-agent` (or your preferred name)
   - **Region:** Choose closest to your users
   - **Branch:** `main`
   - **Runtime:** `Docker`
   - **Plan:** Start with Free tier or Starter ($7/month)

4. **Set Environment Variables:**
   
   In the Render dashboard, add these environment variables:
   
   | Key | Value | Description |
   |-----|-------|-------------|
   | `GEMINI_API_KEY` | Your Gemini API key | Get from Google AI Studio |
   | `SUPABASE_URL` | Your Supabase URL | From Supabase project settings |
   | `SUPABASE_KEY` | Your Supabase key | From Supabase project settings |
   | `TABLE_NAME` | `documents` | Your table name in Supabase |
   | `PORT` | `8501` | Streamlit default port |

5. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your Docker container
   - First deployment takes 5-10 minutes

### 3. Get Your API Keys

#### Google Gemini API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

#### Supabase Credentials:
1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy:
   - **URL** (Project URL)
   - **anon/public key** or **service_role key**

### 4. Prepare Supabase Database

Create a table with text content:

```sql
-- Example table structure
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  title VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insert sample data
INSERT INTO documents (content, title) VALUES
('Artificial Intelligence is transforming how we work and live.', 'AI Overview'),
('Machine learning models require large amounts of data for training.', 'ML Basics'),
('RAG systems combine retrieval and generation for better responses.', 'RAG Systems');
```

### 5. Monitor Deployment

1. Check the **Logs** tab in Render dashboard
2. Look for "You can now view your Streamlit app"
3. Your app URL will be: `https://your-service-name.onrender.com`

## 🔧 Troubleshooting

### Build Failures
- Check Docker logs in Render dashboard
- Verify all files are committed to GitHub
- Ensure requirements.txt has correct versions

### Runtime Errors
- Check environment variables are set correctly
- Verify Supabase credentials
- Test Gemini API key validity
- Check table exists in Supabase

### Slow Performance
- Upgrade to a paid Render plan (Free tier spins down after inactivity)
- Optimize embedding model (consider smaller models)
- Add caching for frequently accessed data

## 💰 Cost Estimation

### Render.com:
- **Free Tier:** $0 (spins down after 15 min inactivity)
- **Starter:** $7/month (always running)
- **Standard:** $25/month (more resources)

### Google Gemini API:
- Free tier: 60 requests/minute
- Check [current pricing](https://ai.google.dev/pricing)

### Supabase:
- Free tier: 500MB database, 2GB bandwidth
- Check [current pricing](https://supabase.com/pricing)

## 🔄 Updating Your App

1. Make changes to your code
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Update: description"
git push
```
3. Render automatically rebuilds and redeploys

## 🛡️ Security Best Practices

1. **Never commit API keys** to GitHub
2. Use Render environment variables for secrets
3. Use Supabase Row Level Security (RLS) policies
4. Enable HTTPS (automatic on Render)
5. Regularly rotate API keys

## 📊 Monitoring

- **Render Dashboard:** Monitor CPU, memory, requests
- **Logs:** Real-time application logs
- **Metrics:** Response times, error rates
- Set up alerts for downtime

## 🎯 Next Steps

- Add user authentication
- Implement rate limiting
- Add database caching
- Set up CI/CD pipeline
- Add unit tests
- Configure custom domain

## 📞 Support Resources

- [Render Documentation](https://render.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Supabase Documentation](https://supabase.com/docs)
- [Google Gemini API Docs](https://ai.google.dev/docs)

---

**Need Help?** Check the logs first, then consult the relevant documentation above.
