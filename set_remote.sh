#!/bin/bash

# Define your remotes
GITHUB_SSH="git@github.com:WL040930/mp4_2_mp3.git"
HF="https://huggingface.co/spaces/WL040930/mp4_2_mp3"

echo "Select a remote to set as origin:"
echo "1) GitHub (SSH)"
echo "2) Hugging Face"

read -p "Enter your choice [1-2]: " choice

case $choice in
    1)
        git remote set-url origin "$GITHUB_SSH" 2>/dev/null || git remote add origin "$GITHUB_SSH"
        echo "✅ Remote set to GitHub (SSH): $GITHUB_SSH"
        ;;
    2)
        git remote set-url origin "$HF" 2>/dev/null || git remote add origin "$HF"
        echo "✅ Remote set to Hugging Face: $HF"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Current remotes:"
git remote -v