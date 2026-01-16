# Vercel Deployment Guide for VerifAI

This guide will help you deploy your VerifAI Flask application to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Your project pushed to GitHub (already done ✅)
3. All environment variables ready

## Deployment Steps

### Method 1: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit [vercel.com](https://vercel.com) and log in
   - Click "Add New Project" or "Import Project"

2. **Import Your Repository**
   - Select GitHub as your Git provider
   - Find and select `RsEg7777/VerifAI` repository
   - Click "Import"

3. **Configure Project Settings**
   - **Framework Preset**: Other (or Python)
   - **Root Directory**: `./` (root of the project)
   - **Build Command**: Leave empty (or `pip install -r requirements.txt` if needed)
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt`

4. **Set Environment Variables**
   Go to Settings → Environment Variables and add:
   
   ```
   SECRET_KEY=your-secret-key-here
   GOOGLE_API_KEY=your-google-api-key
   GOOGLE_CSE_ID=your-google-cse-id
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   SIGHTENGINE_API_USER=your-sightengine-user
   SIGHTENGINE_API_SECRET=your-sightengine-secret
   DATABASE_URL=sqlite:///newsguard.db
   ```
   
   **Note**: For production, consider using PostgreSQL instead of SQLite. You can use Vercel Postgres or an external database service.

5. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your app will be live at `your-project-name.vercel.app`

### Method 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   # Preview deployment
   vercel
   
   # Production deployment
   vercel --prod
   ```

4. **Set Environment Variables**
   ```bash
   vercel env add SECRET_KEY
   vercel env add GOOGLE_API_KEY
   vercel env add GOOGLE_CSE_ID
   # ... add all other environment variables
   ```

## Important Notes

### Database Considerations

- **SQLite**: SQLite files are ephemeral on Vercel serverless functions. Each function invocation gets a fresh filesystem.
- **Recommended**: Use an external database service:
  - Vercel Postgres (recommended)
  - Supabase
  - PlanetScale
  - Railway
  - Any PostgreSQL/MySQL database

### Updating Database Configuration

If using PostgreSQL, update your `config.py`:

```python
# In config.py, update DATABASE_URL
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///newsguard.db')
```

For Vercel Postgres, the connection string format is:
```
postgresql://user:password@host:port/database
```

### Limitations

1. **File Uploads**: Vercel has a 4.5MB limit for request body size. For larger file uploads, consider using a service like Cloudinary or AWS S3.

2. **Execution Time**: Vercel serverless functions have execution time limits:
   - Hobby: 10 seconds
   - Pro: 60 seconds
   - Enterprise: 900 seconds

3. **Cold Starts**: First request after inactivity may be slower due to cold starts.

4. **Ollama Integration**: If you're using Ollama locally, you'll need to:
   - Use a cloud-based LLM service (OpenAI, Anthropic, etc.)
   - Or deploy Ollama separately and call it via API

### Troubleshooting

1. **Build Fails**
   - Check build logs in Vercel dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **Function Timeout**
   - Optimize long-running operations
   - Consider breaking into smaller functions
   - Use background jobs for heavy processing

3. **Database Issues**
   - Ensure database is accessible from Vercel's IP ranges
   - Check connection string format
   - Verify database credentials

4. **Environment Variables Not Working**
   - Ensure variables are set for the correct environment (Production, Preview, Development)
   - Redeploy after adding new environment variables

## Post-Deployment

1. **Test Your Deployment**
   - Visit your Vercel URL
   - Test all major features
   - Check API endpoints

2. **Set Up Custom Domain** (Optional)
   - Go to Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

3. **Monitor Performance**
   - Use Vercel Analytics (if available on your plan)
   - Check function logs in the dashboard
   - Monitor error rates

## Continuous Deployment

Once connected to GitHub, Vercel will automatically:
- Deploy on every push to `main` branch (production)
- Create preview deployments for pull requests
- Deploy previews for other branches

## Support

- Vercel Documentation: https://vercel.com/docs
- Vercel Community: https://github.com/vercel/vercel/discussions
