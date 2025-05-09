# Movie Recommendation System - Deployment Guide

This guide provides instructions for deploying this Django-based movie recommendation system on Railway.

## Prerequisites

- A Railway account (https://railway.app/)
- Git installed on your local machine
- GitHub repository for your project

## Project Setup

This project has been configured for deployment with the following files:

- `Procfile`: Defines the command to run the web server
- `runtime.txt`: Specifies the Python version
- `requirements.txt`: Lists all dependencies
- `railway.json`: Railway configuration file
- `.env.example`: Template for environment variables

## Deployment Steps

### 1. Prepare Your Environment Variables

Create a `.env` file based on the provided `.env.example` template and set your environment variables:

```
SECRET_KEY=your_secure_secret_key
DEBUG=False
ALLOWED_HOSTS=.railway.app,localhost,127.0.0.1
DATABASE_URL=your_database_url
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
GROQ_API_KEY=your_groq_api_key
```

### 2. Deploy to Railway

#### Option 1: Deploy via Railway CLI

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

4. Deploy your application:
   ```
   railway up
   ```

#### Option 2: Deploy via GitHub Integration

1. Push your code to GitHub
2. Log in to Railway dashboard
3. Create a new project and select "Deploy from GitHub repo"
4. Select your repository
5. Configure environment variables in the Railway dashboard
6. Railway will automatically deploy your application

### 3. Database Setup

Railway provides PostgreSQL as a service:

1. Add a PostgreSQL database from the Railway dashboard
2. Railway will automatically set the `DATABASE_URL` environment variable
3. Run migrations after deployment:
   ```
   railway run python src/manage.py migrate
   ```

### 4. Static Files

Static files are handled by WhiteNoise, which is already configured in the project settings.

### 5. Verify Deployment

1. Once deployed, Railway will provide a URL for your application
2. Visit the URL to verify that your application is running correctly

## Troubleshooting

- Check Railway logs for any deployment errors
- Ensure all environment variables are correctly set
- Verify that the database connection is working
- Make sure migrations have been applied

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/en/stable/)