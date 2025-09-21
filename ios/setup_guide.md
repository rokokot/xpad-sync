# iOS Setup Guide

This guide walks you through setting up iOS Shortcuts to automatically process Xpad notes received via Pushcut notifications and save them to Apple Notes.

## Overview

**Workflow**: Pushcut Notification → iOS Shortcuts → Apple Notes

## Prerequisites

- ✅ Zapier automation configured and working
- ✅ iOS device (iPhone/iPad) with iOS 14+ 
- ✅ Pushcut app installed
- ✅ Shortcuts app (built-in on iOS)
- ✅ Apple Notes app

## Step 1: Install and Configure Pushcut

### 1.1 Install Pushcut
1. **Download Pushcut** from the App Store
2. **Open the app** and create an account
3. **Enable notifications** when prompted

### 1.2 Get API Key
1. **Open Pushcut app**
2. **Go to "Account" tab**
3. **Copy your API Key** 
4. **Note it down** - you'll need this for Zapier

### 1.3 Create Automation Server
1. **Go to "Automation Server" tab**
2. **Tap "+" to create new automation**
3. **Name**: `ProcessXpadNote`
4. **Action**: `Run Shortcut`
5. **Shortcut**: (we'll select this after creating the shortcut)
6. **Save the automation**

## Step 2: Create ProcessXpadNote Shortcut

### 2.1 Open Shortcuts App
1. **Open Shortcuts app**
2. **Tap "+" to create new shortcut**
3. **Name it**: `ProcessXpadNote`

### 2.2 Build the Shortcut Actions

**Action 1: Get Input from Notification**
1. **Add action**: "Get Contents of Input"
2. **This receives the notification data from Pushcut**

**Action 2: Extract Download URL**
1. **Add action**: "Get Text from Input"
2. **Configure**: Use the input from previous action
3. **Note**: This contains the Google Drive download URL

**Action 3: Download File Content**
1. **Add action**: "Get Contents of URL"
2. **URL**: Use output from previous action
3. **Method**: GET
4. **Headers**: Leave default

**Action 4: Process Note Content**
1. **Add action**: "Get Text from Input"
2. **This converts the downloaded content to text**

**Action 5: Extract Title**
1. **Add action**: "Split Text"
2. **Split by**: Custom (new lines)
3. **Add action**: "Get Item from List"
4. **Get**: First Item
5. **Add action**: "Replace Text"
6. **Find**: `#` (remove markdown headers)
7. **Replace**: (leave empty)

**Action 6: Clean Title**
1. **Add action**: "Replace Text"
2. **Find**: `*` (remove markdown bold/italic)
3. **Replace**: (leave empty)
4. **Add action**: "Replace Text" 
5. **Find**: `_`
6. **Replace**: (leave empty)

**Action 7: Extract Content**
1. **Add action**: "Split Text" (on the original content)
2. **Split by**: `---` (metadata separator)
3. **Add action**: "Get Item from List"
4. **Get**: First Item (main content)

**Action 8: Create Apple Note**
1. **Add action**: "Create Note"
2. **Title**: Use cleaned title from Action 6
3. **Body**: Use content from Action 7
4. **Folder**: Create/select "Xpad Sync" folder

**Action 9: Confirmation (Optional)**
1. **Add action**: "Show Notification"
2. **Title**: "Xpad Note Synced"
3. **Body**: Use title from Action 6

### 2.3 Test the Shortcut
1. **Tap "Play" button** to test
2. **When prompted for input**, paste a sample Google Drive URL
3. **Verify** it creates a note in Apple Notes

## Step 3: Connect Pushcut to Shortcut

### 3.1 Update Pushcut Automation
1. **Open Pushcut app**
2. **Go to "Automation Server"**
3. **Edit "ProcessXpadNote" automation**
4. **Select Shortcut**: Choose "ProcessXpadNote"
5. **Save changes**

### 3.2 Test Integration
1. **Use Pushcut's test feature**:
   - Go to "Automation Server"
   - Tap "Test" on ProcessXpadNote
   - Enter a test URL when prompted

## Step 4: Create XpadNoteOrganizer Shortcut (Optional)

This shortcut helps organize and manage your synced notes.

### 4.1 Create New Shortcut
1. **Name**: `XpadNoteOrganizer`
2. **Add to Home Screen** for easy access

### 4.2 Build Organization Actions

**Action 1: Find Xpad Notes**
1. **Add action**: "Find Notes"
2. **Filter**: Folder is "Xpad Sync"

**Action 2: Choose Organization Method**
1. **Add action**: "Choose from Menu"
2. **Options**: 
   - "By Date"
   - "By Content Type" 
   - "Clean Duplicates"
   - "Export All"

**Action 3: Organize by Date**
1. **Add action**: "Format Date"
2. **Date Format**: "MMMM yyyy" (e.g., "March 2024")
3. **Add action**: "Create Note"
4. **Title**: "Xpad Notes - [Month Year]"
5. **Body**: List of note titles with dates

**Action 4: Content Type Organization**
1. **Add action**: "Get Text from Input"
2. **Add action**: "Match Text" (regex patterns)
3. **Patterns**:
   - `TODO|TASK|REMINDER` → "Tasks"
   - `MEETING|NOTES` → "Meeting Notes"
   - `IDEA|BRAINSTORM` → "Ideas"
4. **Create folders/collections** based on matches

## Step 5: End-to-End Testing

### 5.1 Create Test Note in Xpad
1. **Open Xpad** on Linux
2. **Create note** with content:
   ```
   iOS Test Note
   
   This note should appear in Apple Notes automatically.
   
   TODO: Verify the sync is working
   
   Created: [current time]
   ```

### 5.2 Monitor the Process
1. **Watch file sync** to Google Drive (~5 seconds)
2. **Check Zapier trigger** (~15 seconds)
3. **Receive Pushcut notification** (~30 seconds)
4. **Shortcut processes automatically**
5. **Note appears in Apple Notes** (~45 seconds total)

## Step 6: Automation Settings

### 6.1 Enable Background Processing
1. **Go to iOS Settings**
2. **Shortcuts → Advanced**
3. **Enable "Allow Running Scripts"**
4. **Enable "Allow Sharing Large Amounts of Data"**

### 6.2 Notification Settings
1. **iOS Settings → Notifications → Pushcut**
2. **Enable "Allow Notifications"**
3. **Set "Alert Style" to "Banners" or "Alerts"**
4. **Enable "Badge App Icon"**

### 6.3 Background App Refresh
1. **iOS Settings → General → Background App Refresh**
2. **Enable for Pushcut**
3. **Enable for Shortcuts**

## Troubleshooting

### Shortcut Not Running

**Check Pushcut automation:**
1. Verify automation name matches exactly
2. Ensure shortcut is selected in automation
3. Test automation manually in Pushcut

**Check Shortcuts permissions:**
1. Go to Settings → Shortcuts
2. Enable necessary permissions
3. Try running shortcut manually

### Notes Not Creating

**Check Apple Notes access:**
1. Settings → Privacy → Apple Notes
2. Ensure Shortcuts has access

**Verify folder exists:**
1. Open Apple Notes
2. Create "Xpad Sync" folder if missing
3. Update shortcut to use correct folder

### Content Not Downloading

**Network issues:**
1. Check internet connection
2. Verify Google Drive link is accessible
3. Test URL in Safari first

**URL format issues:**
1. Ensure Zapier sends download URL, not view URL
2. Check URL format in notification

## Advanced Features

### Custom Note Templates
Modify the shortcut to use templates:
```
# [Title]

[Content]

---
**Metadata:**
- Source: Xpad (Linux)
- Synced: [Current Date]
- Device: [Device Name]
```

### Smart Folder Assignment
Auto-assign notes to folders based on content:
- Tasks → "Task Management"
- Meeting notes → "Meetings" 
- Ideas → "Brainstorming"
- Default → "Xpad Sync"

### Reminder Integration
Auto-create reminders for notes containing:
- "TODO", "TASK", "REMINDER"
- Due dates in content
- Priority indicators

## Security and Privacy

- **Local Processing**: All content processing happens on your device
- **No Cloud Analysis**: Content isn't sent to third-party services
- **Apple's Security**: Leverages Apple's secure note encryption
- **Access Control**: Only authorized apps can access your notes

## Next Steps

Once iOS setup is complete:
1. **Test the full workflow** end-to-end
2. **Customize shortcuts** for your workflow
3. **Set up additional automations** if needed
4. **Share shortcuts** with other users

## Shortcut Sharing

To share your configured shortcuts:
1. **Open Shortcuts app**
2. **Select shortcut**
3. **Tap share button**
4. **Choose "Copy iCloud Link"**
5. **Share link** with others

## Support

For iOS-specific issues:
1. Check [Apple's Shortcuts documentation](https://support.apple.com/shortcuts)
2. Review [Pushcut support](https://www.pushcut.io/support)
3. Test each component individually
4. Check iOS version compatibility (iOS 14+ required)