#!/bin/bash
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
# Run this after creating the repository on GitHub

echo "Enter your GitHub username:"
read GITHUB_USERNAME

echo "Enter your repository name (default: ftd-dashboard):"
read REPO_NAME
REPO_NAME=${REPO_NAME:-ftd-dashboard}

git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
git branch -M main
git push -u origin main

echo "✅ Pushed to GitHub! Now go to https://share.streamlit.io to deploy."
