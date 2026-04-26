#!/bin/bash

# ==============================================================================
# HMS Repository Migration & Delta Commit Script (REPAIR VERSION)
# This script migrates the project to the new GitHub repository,
# handles large file exclusions via .gitignore, and commits all deltas.
# ==============================================================================

# Configuration
NEW_REPO_URL="https://github.com/balasubramaniamrk1/HMS.git"
CURRENT_BRANCH=$(git branch --show-current)

# Check if we are in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: This directory is not a git repository."
    exit 1
fi

echo "--- Starting Migration & Repair Process ---"

# 1. Ensure .gitignore exists (was created by assistant)
if [ ! -f .gitignore ]; then
    echo "Warning: .gitignore not found. Creating a basic one..."
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo ".env" >> .gitignore
    echo ".DS_Store" >> .gitignore
fi

# 2. Update the remote URL
echo "Step 1: Updating remote 'origin' to $NEW_REPO_URL"
git remote set-url origin "$NEW_REPO_URL"

# 3. Clean up the index (Remove ignored files that were already staged)
echo "Step 2: Cleaning up Git index (removing ignored files like venv/)..."
git rm -r --cached . > /dev/null 2>&1
git add .

# 4. Commit the changes
# We use --amend if the last commit was the migration attempt, otherwise a new commit.
LAST_COMMIT_MSG=$(git log -1 --pretty=%B)
if [[ "$LAST_COMMIT_MSG" == *"Migration:"* ]]; then
    echo "Step 3: Amending the previous migration commit..."
    git commit --amend -m "Migration: Move to HMS repository and commit delta changes (fixed large files)"
else
    echo "Step 3: Creating a new migration commit..."
    git commit -m "Migration: Move to HMS repository and commit delta changes"
fi

# 5. Push to the new repository
echo "Step 4: Pushing to the new repository (branch: $CURRENT_BRANCH)..."
# We use --force if we amended the commit, though since the previous push failed,
# a normal push might work. We'll try normal first.
git push -u origin "$CURRENT_BRANCH"

if [ $? -eq 0 ]; then
    echo "--- Migration Successfully Completed! ---"
    echo "Your project is now linked to: $NEW_REPO_URL"
else
    echo "--- Push Failed Again! ---"
    echo "If you still see large file errors, we may need to use a tool like 'git-filter-repo' or reset the history."
    exit 1
fi
