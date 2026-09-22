#!/bin/bash

export PATH=/usr/local/bin:/usr/bin:/bin:/root/.local/bin:$PATH

# Build and deploy script for OpenWind Help documentation
# Pulls latest wiki content, builds Hugo site, and deploys to /srv/openwind.ul-renewables.com
# Designed to be run daily via cron

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
WEBSITE_DIR="$REPO_DIR/website"
CONTENT_DIR="$WEBSITE_DIR/content"
BUILD_DIR="$WEBSITE_DIR/public"
REMOTE_USER="pablo"
REMOTE_HOST="192.168.17.21"
REMOTE_DEPLOY_DIR="/srv/openwind.ul-renewables.com"
REMOTE_BACKUP_DIR="/srv/openwind.ul-renewables.com.backup"
# Log file location - use home directory for better permissions
LOG_FILE="${LOG_FILE:-$HOME/openwind-build.log}"
TEMP_BUILD_DIR=$(mktemp -d)

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    # Cleanup temp directory
    rm -rf "$TEMP_BUILD_DIR"
    exit 1
}

# Cleanup handler
cleanup() {
    rm -rf "$TEMP_BUILD_DIR"
}

trap cleanup EXIT

log "Starting OpenWind help build and deploy process"

# Change to repo directory
cd "$REPO_DIR" || error_exit "Cannot change to repo directory: $REPO_DIR"

# Reset the deployment checkout to the exact remote main revision
log "Resetting repository to origin/main..."
git fetch origin || error_exit "git fetch failed"
git reset --hard origin/main || error_exit "Failed to reset repository to origin/main"
git clean -fd || error_exit "Failed to remove untracked repository files"

# Check if wiki content exists in backup folder, if so use it
# If not, assume wiki content is already in place or will be manually synced
if [ -d "$REPO_DIR/backup" ] && [ -n "$(ls -A "$REPO_DIR/backup" 2>/dev/null)" ]; then
    log "Copying wiki content from backup folder to website/content..."
    rm -rf "$CONTENT_DIR"
    mkdir -p "$CONTENT_DIR"
    cp -r "$REPO_DIR/backup"/* "$CONTENT_DIR/" || error_exit "Failed to copy wiki content"
else
    log "Note: No wiki backup found. Ensure wiki content is in website/content directory."
fi


# Pull wiki content from GitHub
log "Pulling wiki content from GitHub..."
WIKI_URL="https://github.com/Underwriters-Labs/renewables.openwind.help.wiki.git"
if [ -d "$CONTENT_DIR/.git" ]; then
    # Wiki already cloned, update it
    cd "$CONTENT_DIR" || error_exit "Cannot change to content directory"
    git fetch origin || error_exit "Failed to fetch wiki updates"
    git reset --hard origin/master || error_exit "Failed to reset wiki to remote state"
    git clean -fdx || error_exit "Failed to remove untracked wiki files"
    cd "$REPO_DIR" || error_exit "Cannot change back to repo directory"
else
    # Clone wiki for the first time
    rm -rf "$CONTENT_DIR"
    git clone "$WIKI_URL" "$CONTENT_DIR" || error_exit "Failed to clone wiki repository"
fi


# Run Python orchestration script
log "Running content processing tools..."
python3 "$WEBSITE_DIR/tools/run_all_tools.py" --base "$WEBSITE_DIR" --backup || error_exit "Content processing failed"

# Build Hugo site to temporary location
log "Building Hugo site to temporary directory..."
cd "$WEBSITE_DIR" || error_exit "Cannot change to website directory"
hugo --minify --cleanDestinationDir --destination "$TEMP_BUILD_DIR" || error_exit "Hugo build failed"

# Verify build output exists
if [ ! -d "$TEMP_BUILD_DIR" ] || [ -z "$(ls -A "$TEMP_BUILD_DIR" 2>/dev/null)" ]; then
    error_exit "Hugo build produced no output"
fi

log "Build successful. Deploying to $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR..."

# Create backup on remote server and remove old deployment
log "Removing old deployment and creating backup on remote server..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "
# Remove old backup if it exists
[ -d \"$REMOTE_BACKUP_DIR\" ] && sudo rm -rf \"$REMOTE_BACKUP_DIR\"
# Move current deployment to backup
if [ -d \"$REMOTE_DEPLOY_DIR\" ]; then
    sudo mv \"$REMOTE_DEPLOY_DIR\" \"$REMOTE_BACKUP_DIR\"
fi
# Create fresh deployment directory
sudo mkdir -p \"$REMOTE_DEPLOY_DIR\"
sudo chown $REMOTE_USER:$REMOTE_USER \"$REMOTE_DEPLOY_DIR\"
" || error_exit "Failed to prepare remote deployment directory"

# Deploy using rsync over SSH
log "Syncing built site to remote server..."
rsync -avz --checksum --delete --rsh='ssh' "$TEMP_BUILD_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/" || error_exit "Failed to deploy to remote server"

# Set proper permissions on remote
log "Setting directory permissions on remote server..."
ssh -q "$REMOTE_USER@$REMOTE_HOST" "sudo chmod -R 755 \"$REMOTE_DEPLOY_DIR\"" || error_exit "Failed to set remote directory permissions"

log "Remote deployment completed successfully!"
log "Static site ready at: $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo "${timestamp} - Last run." >> "$LOG_FILE"

exit 0

