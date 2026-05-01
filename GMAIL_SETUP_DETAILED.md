# 📧 GMAIL REAL MODE SETUP - Ultra-Detailed Step-by-Step

**Total Time: 5 minutes**  
**Difficulty: Very Easy**  
**Cost: FREE**

---

## STEP 1: Open Google Cloud Console

1. Open your web browser (Chrome, Edge, Firefox, etc.)
2. Go to this URL: **https://console.cloud.google.com/**
3. You might need to sign in with your Google account (personal Gmail, not work)
4. If you see a "Sign in" button, click it and use any Google account you have

✅ **You're now in Google Cloud Console**

---

## STEP 2: Create a New Project

**You should see Google Cloud Console homepage. Look for "Select a Project" near the top-left.**

1. **At the very top-left**, you'll see a dropdown that says **"Select a Project"** or shows a project name
2. Click on this **"Select a Project"** dropdown
3. A popup panel appears on the right side
4. At the top of this panel, you'll see **"NEW PROJECT"** button
5. Click **"NEW PROJECT"**

**A "New Project" dialog appears with a form:**

6. In the **"Project name"** field, type: `CloudFlow Support`
7. Leave everything else blank (Organization and Location can stay empty)
8. At the bottom, click the blue **"CREATE"** button
9. **Wait 30 seconds** - you'll see a loading animation

✅ **Your project is created**

---

## STEP 3: Enable Gmail API

**You should now be in your new CloudFlow Support project.**

1. At the top of the page, there's a **search box**
2. Click in the search box
3. Type: `gmail api`
4. In the search results, click on **"Gmail API"** (it will have a Gmail icon)
5. You'll be taken to the Gmail API page

**On the Gmail API page:**

6. You'll see a big blue button that says **"ENABLE"**
7. Click the **"ENABLE"** button
8. **Wait 10 seconds** - the page updates automatically

✅ **Gmail API is now enabled**

---

## STEP 4: Create OAuth Credentials

**After Gmail API is enabled, you're still on the Gmail API page.**

1. On the left side, you'll see a menu with options
2. Click on **"Credentials"** (it's in the left menu)
3. You're now on the Credentials page

**Creating new credentials:**

4. Near the top of the page, click the blue **"+ CREATE CREDENTIALS"** button
5. A dropdown menu appears
6. Click on **"OAuth client ID"** from the dropdown

**Configuration dialog appears:**

7. You'll see "Application type" with options
8. Click the dropdown for "Application type"
9. Select **"Desktop app"**
10. Click the blue **"CREATE"** button

✅ **Your OAuth credentials are created**

---

## STEP 5: Download credentials.json

**A popup dialog appears with your credentials.**

1. On the right side of the popup, you'll see a **download icon** (⬇️)
2. Click the **download icon** (⬇️)
3. Your browser downloads a file: `client_secret_XXXXXX.json` (where X's are random characters)
4. The file goes to your **Downloads** folder
5. You can close this popup dialog now

✅ **credentials.json is downloaded**

---

## STEP 6: Copy credentials.json to Project Folder

**Open File Manager (Windows Explorer):**

1. Press **Windows key + E** on your keyboard
2. File Manager opens
3. On the left side, click **"Downloads"**
4. You'll see the `client_secret_*.json` file

**Rename the file:**

5. **Right-click** on `client_secret_*.json`
6. From the popup menu, click **"Rename"**
7. The filename becomes editable (highlighted in blue)
8. Delete the current name and type: `credentials.json`
9. Press **Enter** on your keyboard

**Move the file:**

10. **Right-click** on the now-renamed `credentials.json`
11. Click **"Cut"** from the popup menu
12. In File Manager, navigate to: `C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\`
13. **Right-click** in the empty space
14. Click **"Paste"**

✅ **credentials.json is now in your project folder**

---

## STEP 7: Verify File is in Correct Location

1. In File Manager, make sure you're in: `C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\`
2. You should see `credentials.json` in this folder
3. Double-check the filename is exactly `credentials.json` (not `credentials.json.txt`)

✅ **File is in the correct location**

---

## STEP 8: Restart API Server

**Open a terminal/command prompt:**

1. Press **Windows key + R**
2. Type: `cmd`
3. Press **Enter**
4. A black command prompt window opens

**Stop the current server (if running):**

5. If you see something running in the terminal, press **Ctrl+C** to stop it
6. Wait 2 seconds for it to stop

**Start the server:**

7. Type this command:
   ```
   cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
   ```
8. Press **Enter**
9. Type this command:
   ```
   python -m uvicorn production.api.main:app --reload --port 8000
   ```
10. Press **Enter**

**Watch the output:**

11. The server starts and prints messages
12. Look for this message in the output:
    ```
    ✅ Gmail Real Mode: Using credentials from credentials.json
    ```
13. If you see this message, **Gmail is now in REAL mode** ✅

---

## STEP 9: OAuth Authorization (First Time Only)

**On your FIRST Gmail API call, you'll need to authorize.**

When you make the first request to Gmail:

1. A web browser opens automatically
2. You see a Google sign-in page
3. Sign in with your Google account (any account is fine)
4. You see: **"CloudFlow Support wants to access your Google Account"**
5. Click the blue **"Allow"** button
6. You see: **"Authorization successful"** and **"You can close this window"**
7. Close the browser tab

**After this:**
- The system caches the authorization token
- No more browser popups needed
- Gmail API works automatically

✅ **Gmail is fully activated in REAL mode**

---

## VERIFY GMAIL IS IN REAL MODE

**Open a new terminal/command prompt:**

1. Press **Windows key + R**
2. Type: `cmd`
3. Press **Enter**

**Run this command:**

```bash
curl http://localhost:8000/api/email/health
```

4. Press **Enter**
5. You should see output like:
   ```json
   {
     "channel": "email",
     "mode": "REAL",
     "status": "healthy",
     "ready": true
   }
   ```

**If you see `"mode": "REAL"`, then Gmail is working!** ✅

---

## 🎯 GMAIL SETUP COMPLETE

✅ Google Cloud Project created  
✅ Gmail API enabled  
✅ OAuth credentials created  
✅ credentials.json downloaded and placed  
✅ Server restarted  
✅ Real mode activated  

**Next: Do WhatsApp setup (see WHATSAPP_SETUP_DETAILED.md)**

