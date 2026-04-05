#!/bin/bash
# claudefolio — Deploy to remote server
set -e

REMOTE="${DEPLOY_TARGET:-user@your-server-ip}"
REMOTE_DIR="${DEPLOY_DIR:-/home/\$(echo $REMOTE | cut -d@ -f1)/claudefolio}"

echo "=== Deploying claudefolio to $REMOTE:$REMOTE_DIR ==="

ssh $REMOTE "mkdir -p $REMOTE_DIR/{config,src/{data,analysis,delivery},memory,scripts,logs}"

echo "Copying files..."
scp -r ../config/*.example.json $REMOTE:$REMOTE_DIR/config/
scp -r ../src/* $REMOTE:$REMOTE_DIR/src/
scp ../requirements.txt ../setup.py $REMOTE:$REMOTE_DIR/

echo "=== Deploy complete. Run 'python3 setup.py' on the server to configure. ==="
