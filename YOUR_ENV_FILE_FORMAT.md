# ✅ Correct .env File Format

## ⚠️ Important: JSON Must Be on ONE LINE

Your `.env` file format is **almost correct**, but the JSON needs to be on a **single line** with escaped quotes.

## ✅ Correct Format:

Create a file named `.env` in your project root with this format:

```env
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"YOUR_PROJECT_ID","private_key_id":"YOUR_PRIVATE_KEY_ID","private_key":"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n","client_email":"YOUR_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com","client_id":"YOUR_CLIENT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/..."}

GOOGLE_SHEETS_SPREADSHEET_ID=1l48px8Sj9JiqbfW8aLgMeWMMGAVYQFjbKnZWZkVmDCE

GOOGLE_SHEETS_WORKSHEET_NAME=medicare-form
```

## 🔧 Key Changes:

1. **JSON on ONE line** - No line breaks in the JSON
2. **Escaped newlines** - `\n` becomes `\\n` in the private_key
3. **No extra spaces** - Remove any extra whitespace

## 📝 How to Create It:

### Option 1: Use the Provided Format Above
Copy the format above and replace with your actual values.

### Option 2: Convert Your JSON to Single Line

1. **Take your JSON file** (the one you downloaded)
2. **Remove all line breaks** - Make it one continuous line
3. **Escape the newlines** in private_key: Change `\n` to `\\n`
4. **Wrap in quotes** and put it after `GOOGLE_SHEETS_CREDENTIALS_JSON=`

## ✅ Your Values (Already Correct):

- ✅ `GOOGLE_SHEETS_SPREADSHEET_ID=1l48px8Sj9JiqbfW8aLgMeWMMGAVYQFjbKnZWZkVmDCE` - **Correct!**
- ✅ `GOOGLE_SHEETS_WORKSHEET_NAME=medicare-form` - **Correct!**

## 🚀 After Creating .env File:

1. **Install python-dotenv** (if not already installed):
   ```bash
   pip install python-dotenv
   ```

2. **Create `.env` file** in your project root with the format above

3. **Restart your app:**
   ```bash
   python app.py
   ```

4. **Test it** - Submit a form and check your Google Sheet!

## 🔒 Security Note:

- **Never commit `.env` file to git!**
- Add `.env` to your `.gitignore` file
- The `.env` file contains sensitive credentials

---

**Once you format the JSON on one line, your .env file will work perfectly!** ✅

