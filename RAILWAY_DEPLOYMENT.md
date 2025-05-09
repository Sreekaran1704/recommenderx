# Railway Deployment Guide for Movie Recommendation System

## Overview

This guide provides detailed instructions for deploying this Django-based movie recommendation system on Railway.app. Railway is a modern platform that makes it easy to deploy web applications without complex infrastructure setup.

## Prerequisites

- A Railway account (Sign up at [railway.app](https://railway.app/))
- Git installed on your local machine
- Your project code pushed to a GitHub repository

## Configuration Files

The following files have been prepared for Railway deployment:

1. **Procfile**: Defines the command to run the web server
   ```
   web: gunicorn recommenderx.wsgi --log-file -
   ```

2. **runtime.txt**: Specifies the Python version
   ```
   python-3.11.0
   ```

3. **requirements.txt**: Lists all dependencies including deployment-specific packages:
   - gunicorn: WSGI HTTP server
   - whitenoise: Static file serving
   - dj-database-url: Database URL configuration

4. **railway.json**: Railway configuration file
   ```json
   {
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "python -m pip install -r requirements.txt && python src/manage.py collectstatic --noinput"
     },
     "deploy": {
       "startCommand": "cd src && gunicorn recommenderx.wsgi",
       "healthcheckPath": "/",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

5. **settings_production.py**: Production-ready Django settings
   - Configures environment variables
   - Sets up WhiteNoise for static files
   - Configures database with dj-database-url

## Deployment Steps

### 1. Environment Variables

You'll need to set the following environment variables in Railway:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to 'False' for production
- `ALLOWED_HOSTS`: Set to '.railway.app,localhost,127.0.0.1'
- `DATABASE_URL`: Railway will automatically set this
- `RAILWAY_ENVIRONMENT`: Set to 'production'
- `CLERK_PUBLISHABLE_KEY`: Your Clerk publishable key
- `CLERK_SECRET_KEY`: Your Clerk secret key
- `GROQ_API_KEY`: Your GROQ API key

### 2. Deploy to Railway

#### Option 1: Deploy via Railway Dashboard

1. Log in to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your GitHub repository
4. Configure environment variables in the "Variables" tab
5. Railway will automatically deploy your application

#### Option 2: Deploy via Railway CLI

1. Install Railway CLI:
   ```
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```
   railway login
   ```

3. Link your project:
   ```
   railway link
   ```

4. Set environment variables:
   ```
   railway variables set SECRET_KEY=your_secret_key
   railway variables set DEBUG=False
   railway variables set ALLOWED_HOSTS=.railway.app,localhost,127.0.0.1
   railway variables set RAILWAY_ENVIRONMENT=production
   railway variables set CLERK_PUBLISHABLE_KEY=your_clerk_key
   railway variables set CLERK_SECRET_KEY=your_clerk_secret
   railway variables set GROQ_API_KEY=your_groq_key
   ```

5. Deploy your application:
   ```
   railway up
   ```

### 3. Database Setup

1. Add a PostgreSQL database from the Railway dashboard:
   - Go to "New" → "Database" → "PostgreSQL"
   - Railway will automatically set the `DATABASE_URL` environment variable

2. Run migrations after deployment:
   ```
   railway run python src/manage.py migrate
   ```

### 4. Static Files

Static files are handled by WhiteNoise, which is configured in the production settings. The deployment process will automatically collect static files during the build phase.

### 5. Verify Deployment

1. Once deployed, Railway will provide a URL for your application
2. Visit the URL to verify that your application is running correctly
3. Check the logs in the Railway dashboard for any errors

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify that the PostgreSQL service is properly linked
   - Check that migrations have been applied

2. **Static Files Not Loading**
   - Ensure `collectstatic` ran successfully during deployment
   - Verify WhiteNoise is properly configured in settings and middleware

3. **Application Errors**
   - Check Railway logs for detailed error messages
   - Temporarily set `DEBUG=True` to get more detailed error pages

### Debugging

- Use Railway logs to diagnose issues:
  ```
  railway logs
  ```

- Connect to your PostgreSQL database:
  ```
  railway connect
  ```

## Maintenance

### Updating Your Application

1. Push changes to your GitHub repository
2. Railway will automatically redeploy if you've set up GitHub integration
3. Or manually deploy using the CLI:
   ```
   railway up
   ```

### Database Backups

Regularly backup your database using Railway's backup feature or by running:
```
railway run pg_dump -U postgres > backup.sql
```

## Security Considerations

1. Never commit sensitive information like API keys or passwords to your repository
2. Use environment variables for all sensitive information
3. Keep `DEBUG=False` in production
4. Regularly update dependencies to patch security vulnerabilities

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/en/stable/)
- [dj-database-url Documentation](https://github.com/jazzband/dj-database-url)