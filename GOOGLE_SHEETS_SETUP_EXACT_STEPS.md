# 📊 Google Sheets Setup - EXACT Step-by-Step Instructions

## 🎯 What You Need:

1. ✅ A Google account (Gmail account)
2. ✅ A Google Spreadsheet (we'll create one)
3. ✅ Google Cloud Project (we'll create one)
4. ✅ Service Account credentials (we'll generate them)

---

## 📋 STEP-BY-STEP SETUP:

### STEP 1: Create a Google Spreadsheet

1. **Go to:** https://sheets.google.com
2. **Click:** "Blank" to create a new spreadsheet
3. **Name it:** "Form Submissions" (or any name you want)
4. **IMPORTANT:** Copy the Spreadsheet ID from the URL
   - URL looks like: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`
   - Copy the long string between `/d/` and `/edit`
   - **Example:** If URL is `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit`
   - **Spreadsheet ID is:** `1a2b3c4d5e6f7g8h9i0j`
   - **SAVE THIS - You'll need it later!**

---

### STEP 2: Create Google Cloud Project

1. **Go to:** https://console.cloud.google.com
2. **Sign in** with your Google account
3. **Click:** "Select a project" dropdown at the top
4. **Click:** "New Project"
5. **Project name:** `Form Submission Service` (or any name)
6. **Click:** "Create"
7. **Wait** for project to be created (takes 10-30 seconds)
8. **Click:** "Select Project" if it doesn't auto-select

---

### STEP 3: Enable Google Sheets API

1. **In Google Cloud Console**, click the **☰ (hamburger menu)** top left
2. **Click:** "APIs & Services" → "Library"
3. **Search for:** "Google Sheets API"
4. **Click:** "Google Sheets API"
5. **Click:** "ENABLE" button
6. **Wait** for it to enable (5-10 seconds)

---

### STEP 4: Enable Google Drive API

1. **Still in "APIs & Services" → "Library"**
2. **Search for:** "Google Drive API"
3. **Click:** "Google Drive API"
4. **Click:** "ENABLE" button
5. **Wait** for it to enable (5-10 seconds)

---

### STEP 5: Create Service Account

1. **In Google Cloud Console**, click **☰ (hamburger menu)**
2. **Click:** "APIs & Services" → "Credentials"
3. **Click:** "CREATE CREDENTIALS" button (top of page)
4. **Click:** "Service account"
5. **Service account name:** `form-submission-service` (or any name)
6. **Service account ID:** (auto-filled, leave as is)
7. **Click:** "CREATE AND CONTINUE"
8. **Role:** Leave blank or select "Editor" (optional)
9. **Click:** "CONTINUE"
10. **Click:** "DONE" (skip optional steps)

---

### STEP 6: Create Service Account Key (JSON File)

1. **Still on "Credentials" page**, find your service account you just created
2. **Click** on the service account email (looks like: `form-submission-service@your-project.iam.gserviceaccount.com`)
3. **Click:** "KEYS" tab at the top
4. **Click:** "ADD KEY" → "Create new key"
5. **Select:** "JSON" format
6. **Click:** "CREATE"
7. **JSON file downloads automatically** - Save it somewhere safe!
8. **IMPORTANT:** This file contains sensitive credentials - don't share it!

---

### STEP 7: Share Spreadsheet with Service Account

1. **Go back to your Google Spreadsheet** (https://sheets.google.com)
2. **Open** the spreadsheet you created in Step 1
3. **Click:** "Share" button (top right)
4. **In "Add people and groups" box**, paste the **service account email**
   - Service account email looks like: `form-submission-service@your-project-123456.iam.gserviceaccount.com`
   - You can find it in the JSON file you downloaded (look for `"client_email"`)
5. **Change permission** from "Viewer" to **"Editor"**
6. **UNCHECK** "Notify people" (service account doesn't need email)
7. **Click:** "Share"
8. **Click:** "Done"

---

### STEP 8: Get Credentials from JSON File

1. **Open** the JSON file you downloaded in Step 6
2. **It looks like this:**
```json
{
  "type": "service_account",
  "project_id": "your-project-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "form-submission-service@your-project-123456.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

3. **Copy the ENTIRE JSON content** (all of it, from `{` to `}`)

---

### STEP 9: Set Environment Variables

You need to set these environment variables. Choose one method:

#### Method A: Set in Your Code (For Testing)

Edit `app.py` and add these lines at the top (after the imports):

```python
# Google Sheets Configuration (TEMPORARY - for testing)
os.environ['GOOGLE_SHEETS_CREDENTIALS_JSON'] = '''{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}'''

os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = 'your-spreadsheet-id-here'
os.environ['GOOGLE_SHEETS_WORKSHEET_NAME'] = 'Form Submissions'
```

**IMPORTANT:** 
- Replace `your-spreadsheet-id-here` with the ID you copied in Step 1
- Replace the JSON with your actual JSON from Step 8
- Escape newlines: Change `\n` to `\\n` in the private_key

#### Method B: Set as Environment Variables (For Production)

**Windows PowerShell:**
```powershell
$env:GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id",...}'
$env:GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id'
$env:GOOGLE_SHEETS_WORKSHEET_NAME='Form Submissions'
```

**Windows Command Prompt:**
```cmd
set GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
set GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
set GOOGLE_SHEETS_WORKSHEET_NAME=Form Submissions
```

**Linux/Mac:**
```bash
export GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project-id",...}'
export GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id'
export GOOGLE_SHEETS_WORKSHEET_NAME='Form Submissions'
```

---

## ✅ TESTING:

1. **Start your app:**
   ```bash
   python app.py
   ```

2. **Login** to your portal (agent1 / password123)

3. **Go to:** "Submit Form"

4. **Fill out** and submit a test form

5. **Check your Google Spreadsheet** - you should see a new row with:
   - Timestamp
   - Agent name
   - All form fields
   - TrustedForm Certificate URL
   - Proxy IP
   - Submission status

---

## 🔧 TROUBLESHOOTING:

### Error: "Worksheet not found"
- **Fix:** The worksheet will be created automatically on first submission
- Or manually create a worksheet named "Form Submissions"

### Error: "Permission denied"
- **Fix:** Make sure you shared the spreadsheet with the service account email
- Make sure you gave it "Editor" permission (not "Viewer")

### Error: "Invalid credentials"
- **Fix:** Check that the JSON is copied correctly
- Make sure newlines are escaped (`\n` → `\\n`)
- Make sure the entire JSON is on one line if using environment variables

### Error: "API not enabled"
- **Fix:** Go back to Step 3 and 4, make sure both APIs are enabled

---

## 📝 QUICK REFERENCE:

**What you need:**
1. ✅ Spreadsheet ID (from Step 1)
2. ✅ Service Account JSON file (from Step 6)
3. ✅ Service Account email (from JSON file, for sharing)

**Environment Variables:**
- `GOOGLE_SHEETS_CREDENTIALS_JSON` - Entire JSON file content
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Spreadsheet ID
- `GOOGLE_SHEETS_WORKSHEET_NAME` - Worksheet name (optional, defaults to "Form Submissions")

---

## 🎯 SUMMARY:

1. ✅ Create spreadsheet → Get Spreadsheet ID
2. ✅ Create Google Cloud project
3. ✅ Enable Sheets API + Drive API
4. ✅ Create service account
5. ✅ Download JSON key file
6. ✅ Share spreadsheet with service account email
7. ✅ Set environment variables with JSON and Spreadsheet ID
8. ✅ Test by submitting a form

**That's it!** Once set up, every form submission will automatically save to your Google Sheet! 🎉

