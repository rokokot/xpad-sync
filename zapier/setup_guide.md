# Zapier Setup Guide

Complete guide for setting up Zapier automation to bridge Google Drive and iOS Shortcuts.

## Overview

This Zapier automation monitors your Google Drive sync folder and triggers iOS notifications when new Xpad notes are created or modified.

**Flow**: Google Drive (New File) → Zapier → Pushcut (iOS Notification) → iOS Shortcuts

## Prerequisites

- ✅ Xpad to Google Drive sync installed and working
- ✅ Google Drive Desktop client syncing the XpadSync folder
- ✅ Zapier account (free tier works fine)
- ✅ Pushcut app installed on iOS device
- ✅ iOS Shortcuts app

## Step 1: Create New Zap

1. **Login to Zapier**: Go to [zapier.com](https://zapier.com) and sign in
2. **Create Zap**: Click "Create Zap" button
3. **Name your Zap**: "Xpad Notes to iOS" (or similar)

## Step 2: Configure Google Drive Trigger

### 2.1 Choose Trigger App
1. **Search for "Google Drive"** in the app selector
2. **Select "Google Drive"** from the results
3. **Choose trigger event**: "New File in Folder"
4. **Click "Continue"**

### 2.2 Connect Google Drive Account
1. **Click "Sign in to Google Drive"**
2. **Authorize Zapier** to access your Google Drive
3. **Select your Google account** (the one with your XpadSync folder)
4. **Grant permissions** when prompted

### 2.3 Configure Trigger Settings
1. **Folder**: 
   - Click "Choose folder"
   - Navigate to your XpadSync folder (e.g., `/XpadSync` or `/GoogleDrive/XpadSync`)
   - Select the folder and click "Choose"

2. **File Extensions** (Optional but recommended):
   - Enable "File Extensions" filter
   - Add: `md,txt`
   - This ensures only note files trigger the automation

3. **Trigger for**: Select "Files only" (not folders)

4. **Include Shared Drives**: Leave unchecked (unless your folder is in a shared drive)

### 2.4 Test the Trigger
1. **Click "Test trigger"**
2. **Create a test file**: 
   ```bash
   echo "Test note for Zapier" > ~/GoogleDrive/XpadSync/test_zapier.txt
   ```
3. **Wait 1-2 minutes** for Google Drive to sync
4. **Click "Retest"** in Zapier
5. **Verify**: You should see your test file in the results
6. **Click "Continue"**

## Step 3: Add Filter (Recommended)

Adding a filter prevents triggering on non-Xpad files and system files.

### 3.1 Add Filter Step
1. **Click "+ Add a step"**
2. **Choose "Filter"** from the options
3. **Click "Continue"**

### 3.2 Configure Filter Rules
**Rule 1 - File Name Filter**:
- **Field**: Choose "File Name" from the Google Drive trigger data
- **Condition**: "Starts with"
- **Value**: `xpad_note_`

**Rule 2 - File Size Filter** (optional):
- Click "AND" to add another condition
- **Field**: Choose "File Size" from the Google Drive trigger data  
- **Condition**: "Is less than"
- **Value**: `10485760` (10MB in bytes)

### 3.3 Test Filter
1. **Click "Test step"**
2. **Verify**: The test should pass if your test file matches the filter
3. **Click "Continue"**

## Step 4: Configure Pushcut Action

### 4.1 Choose Action App
1. **Search for "Pushcut"** in the app selector
2. **Select "Pushcut"** from the results
3. **Choose action**: "Send Notification"
4. **Click "Continue"**

### 4.2 Connect Pushcut Account
1. **Click "Sign in to Pushcut"**
2. **Follow the authorization flow**
3. **Note**: You'll need the Pushcut app installed on your iOS device first

### 4.3 Configure Notification Settings

**Basic Settings**:
- **Title**: `New Xpad Note`
- **Text**: 
  ```
  {{1. File Name}} created
  Size: {{1. File Size}} bytes
  ```
- **URL**: `{{1. File Web View Link}}`
- **Sound**: `default`

**Advanced Settings**:
- **Input**: `{{1. File Download URL}}`
- **Badge**: `1`
- **Automation Name**: `ProcessXpadNote`

**Important**: The "Automation Name" must exactly match your iOS Shortcut automation name.

### 4.4 Test the Action
1. **Click "Test step"**
2. **Check your iOS device**: You should receive a Pushcut notification
3. **Verify content**: The notification should contain file information
4. **Click "Continue"**

## Step 5: Review and Activate

### 5.1 Review Your Zap
1. **Check all steps**: Trigger → Filter → Action
2. **Verify test results**: All steps should show green checkmarks
3. **Review settings**: Ensure all configuration is correct

### 5.2 Name and Activate
1. **Give your Zap a descriptive name**: "Xpad Notes to iOS via Pushcut"
2. **Click "Publish"** or "Turn on Zap"
3. **Confirm activation**: The Zap should now be live

## Step 6: End-to-End Testing

### 6.1 Create Test Note in Xpad
1. **Open Xpad** on your Linux system
2. **Create a new note**:
   ```
   Test Note from Xpad
   
   This is a test note to verify the complete sync pipeline.
   Created at: [current time]
   ```
3. **Save the note**

### 6.2 Monitor the Pipeline
1. **Wait 2-5 seconds**: File should appear in Google Drive
2. **Wait 15-30 seconds**: Zapier should trigger
3. **Check iOS device**: You should receive a Pushcut notification
4. **Verify Zap history**: Check Zapier dashboard for successful execution

### 6.3 Troubleshoot if Needed
If the test fails, check:
- ✅ Google Drive Desktop is running and syncing
- ✅ File appears in the correct Google Drive folder
- ✅ Zapier filter allows the file through
- ✅ Pushcut notifications are enabled on iOS
- ✅ Internet connection is stable

## Zapier Configuration Summary

Here's a quick reference of your final Zap configuration:

```
📁 TRIGGER: Google Drive - New File in Folder
   ├── Folder: /XpadSync
   ├── File Extensions: md,txt
   └── Trigger for: Files only

🔍 FILTER: Only Xpad Files
   ├── File Name starts with "xpad_note_"
   └── File Size less than 10MB

📱 ACTION: Pushcut - Send Notification
   ├── Title: "New Xpad Note"
   ├── Text: "{{File Name}} created"
   ├── URL: {{File Web View Link}}
   ├── Input: {{File Download URL}}
   └── Automation: ProcessXpadNote
```

## Common Issues and Solutions

### Issue: Zap Not Triggering
**Symptoms**: Files appear in Google Drive but Zapier doesn't trigger

**Solutions**:
1. **Check folder path**: Ensure Zapier is monitoring the correct folder
2. **Verify permissions**: Re-authorize Google Drive access in Zapier
3. **Test manually**: Upload a file directly to Google Drive to test
4. **Check filter**: Temporarily disable filter to see if it's blocking files

### Issue: Multiple Triggers for Same File
**Symptoms**: Getting multiple notifications for the same note

**Solutions**:
1. **Adjust debounce**: Increase `debounce_seconds` in xpad config
2. **Check Google Drive**: Ensure files aren't being modified repeatedly
3. **Add unique filter**: Use file hash in filename to prevent duplicates

### Issue: Pushcut Notifications Not Received
**Symptoms**: Zapier shows success but no iOS notification

**Solutions**:
1. **Check Pushcut app**: Ensure it's installed and logged in
2. **Verify notification settings**: Check iOS notification permissions
3. **Test Pushcut directly**: Send a test notification from Pushcut app
4. **Check automation name**: Must exactly match iOS Shortcuts automation

### Issue: File Content Not Accessible
**Symptoms**: Notification received but can't read file content in iOS

**Solutions**:
1. **Check download URL**: Verify the file download URL is correct
2. **Test file access**: Try opening the file manually in Google Drive
3. **Check permissions**: Ensure file is accessible (not private)
4. **Verify encoding**: Check file is saved as UTF-8

## Advanced Configuration

### Multiple Folders
To monitor multiple folders, create separate Zaps for each folder or use Zapier's "Multiple Folders" feature in paid plans.

### Custom Filtering
Add more sophisticated filters based on:
- File modification time
- File content (using Google Drive's search capabilities)
- File creator
- Specific keywords in filename

### Webhook Alternative
For advanced users, you can replace Pushcut with webhooks directly to iOS Shortcuts (requires iOS 14+):

```
ACTION: Webhooks - POST
URL: [Your iOS Shortcuts webhook URL]
Payload: {"filename": "{{File Name}}", "url": "{{File Download URL}}"}
```

## Monitoring and Maintenance

### Check Zap Health
1. **Monthly**: Review Zap history for errors
2. **Check task usage**: Monitor Zapier task consumption
3. **Test end-to-end**: Periodically verify the complete pipeline

### Update Notifications
If you change your Google Drive folder structure:
1. Update the folder path in Zapier trigger
2. Test with a new file
3. Update any hardcoded paths in your configuration

---

**Next Step**: After Zapier is working, proceed to [iOS Setup Guide](../ios/setup_guide.md) to configure the iOS Shortcuts that process these notifications.