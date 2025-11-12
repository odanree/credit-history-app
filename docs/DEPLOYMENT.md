# Credit History App - Render Deployment Guide

## Quick Deploy to Render

### 1. Push to GitHub
```bash
git add .
git commit -m "build: add Render deployment configuration"
git push origin master
```

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### 3. Deploy Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `odanree/credit-history-app`
3. Render will auto-detect `render.yaml` configuration
4. Click **"Apply"**

### 4. Set Environment Variables
Go to your service → **Environment** tab and add:

```
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox
PLAID_ACCESS_TOKEN=your_plaid_access_token
EXPERIAN_CLIENT_ID=your_experian_client_id
EXPERIAN_CLIENT_SECRET=your_experian_client_secret
EXPERIAN_ENV=sandbox
```

**Important:** Copy these from your local `.env` file

### 5. Deploy
- Render will automatically build and deploy
- Build time: ~2-3 minutes
- Your app will be live at: `https://credit-history-app.onrender.com`

## Free Tier Limitations

⚠️ **Cold Starts**: Free tier spins down after 15 minutes of inactivity
- First request after sleep: ~30 seconds to wake up
- Subsequent requests: instant

💡 **Upgrade to Paid ($7/month)** for:
- Always-on service
- No cold starts
- Better performance

## Manual Deployment (Alternative)

If you don't use `render.yaml`:

1. **Create Web Service**
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

2. **Set Environment Variables** (same as above)

3. **Deploy from GitHub** (auto-deploy on push)

## Troubleshooting

### Build Fails
- Check Python version in `render.yaml` matches your local version
- Verify all dependencies in `requirements.txt`

### App Crashes
- Check logs in Render dashboard
- Verify environment variables are set correctly
- Ensure `PLAID_ACCESS_TOKEN` is valid

### Slow Response
- Normal on free tier (cold starts)
- Upgrade to paid tier for better performance

## Local Development

Still works the same:
```bash
.\.venv\Scripts\python.exe app.py
```

Visit: http://localhost:5001

## Production URL

After deployment, your app will be available at:
```
https://your-app-name.onrender.com
```

Share this URL to access your credit dashboard from anywhere!

## Security Notes

✅ **Never commit `.env` file** (already in `.gitignore`)
✅ **Set environment variables in Render dashboard only**
✅ **Use sandbox credentials until Experian approves production access**

## Next Steps

1. Deploy to Render
2. Test the live URL
3. Wait for Experian support to provision your account
4. Update Experian integration when ready
5. Consider upgrading to paid tier if needed
