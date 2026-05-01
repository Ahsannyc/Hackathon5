# 📋 Complete Guide: Setting Up & Running the Web Form

**Last Updated:** 2026-04-26  
**Difficulty:** Beginner-Friendly ✅  
**Time Required:** 15-20 minutes  

---

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
- ✅ Setup Node.js and npm
- ✅ Install Next.js web form dependencies
- ✅ Configure Tailwind CSS
- ✅ Run the web form locally
- ✅ Submit test data
- ✅ Verify integration with backend

---

## 📋 Prerequisites

Before starting, make sure you have:

### 1. Node.js and npm installed
```bash
# Check if Node.js is installed
node --version

# Check if npm is installed
npm --version
```

**If not installed:**
- Download from: https://nodejs.org/ (LTS version recommended)
- Download latest stable version (18.0 or higher)
- Install following the installer instructions

### 2. Backend API running
- FastAPI server must be running on `http://localhost:8000`
- Run from terminal: `cd production/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### 3. Text editor or IDE
- VS Code (recommended) - https://code.visualstudio.com/
- Or any text editor of your choice

---

## 🚀 Step-by-Step Setup

### Step 1: Navigate to Web Form Directory

Open a new terminal and navigate to the web form folder:

```bash
cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5\production\web-form"
```

**Expected:** Terminal shows the path ending with `\web-form`

---

### Step 2: Install Dependencies

Install all required npm packages:

```bash
npm install
```

**What it does:** Downloads and installs Next.js, React, Tailwind CSS, and other libraries  
**Expected time:** 2-5 minutes  
**Expected output:**
```
added XXX packages in X.XXs
```

**If it fails:**
- Delete `node_modules` folder: `rmdir /s node_modules` (Windows)
- Delete `package-lock.json` file
- Run `npm install` again

---

### Step 3: Verify Installation

Check that required files exist:

```bash
# List files in web-form directory
dir

# Look for these files:
# - package.json
# - next.config.js
# - tailwind.config.js
# - SupportForm.tsx
# - page.tsx
# - layout.tsx
```

---

### Step 4: Start Development Server

Start the Next.js development server:

```bash
npm run dev
```

**Expected output:**
```
▲ Next.js 14.0.0
- Local: http://localhost:3000
- Environments: .env.local

✓ Ready in 3.2s
```

**If port 3000 is in use:**
```bash
# Use a different port
npm run dev -- -p 3001
```

---

### Step 5: Open Web Form in Browser

Open your web browser and go to:

```
http://localhost:3000/web-form
```

**Expected:** You should see a beautiful form with:
- Blue gradient header "Customer Support Form"
- 7 form fields
- Submit button
- Professional styling with shadows

---

## 📝 Understanding the Web Form

### Form Fields

1. **Full Name** (Required)
   - Minimum 2 characters
   - Allows letters, spaces, hyphens, apostrophes
   - Example: "John Smith" ✅, "J" ❌

2. **Email Address** (Required)
   - Must be valid email format
   - Example: "john@example.com" ✅, "john" ❌

3. **Subject** (Required)
   - 5-100 characters
   - Shows character counter
   - Example: "Help with account" ✅, "Help" ❌

4. **Category** (Required dropdown)
   - Options: General, Technical, Billing, Feedback, Bug Report
   - Default: General Inquiry

5. **Priority** (Required dropdown)
   - Options: Low, Medium (default), High
   - Select based on urgency

6. **Message** (Required textarea)
   - 10-5000 characters
   - Shows character counter
   - Example: "I need help with..." ✅, "Need help" ❌

7. **Submit Button**
   - Shows loading spinner while submitting
   - Disabled during submission
   - Shows error or success message

---

## 🧪 Testing the Web Form

### Test 1: Successful Submission

**Steps:**

1. Fill in all fields:
   ```
   Full Name: John Smith
   Email: john@example.com
   Subject: Having trouble with payment
   Category: Billing
   Priority: High
   Message: I tried to upgrade my subscription but the payment keeps failing.
   ```

2. Click "Submit Support Request"

3. **Expected result:**
   - Loading spinner appears for 2-3 seconds
   - Success message displays: "Request submitted successfully!"
   - Ticket ID shows: "TICKET-2026-04-26-001" (or similar)
   - "Submit Another Request" button appears

4. **Check backend logs:**
   - Open terminal running FastAPI
   - Look for: `POST /api/messages/submit - Status: 200`
   - Ticket ID should be logged

---

### Test 2: Validation Errors

**Test required field validation:**

1. Leave "Full Name" empty
2. Click outside the field
3. **Expected:** Red error message: "Name is required"

**Test email validation:**

1. Enter invalid email: "notanemail"
2. Click outside the field
3. **Expected:** Red error message: "Invalid email format"

**Test character limits:**

1. In Subject field, type a very short text: "Hi"
2. Click outside the field
3. **Expected:** Red error message: "Subject must be at least 5 characters"

---

### Test 3: Character Counters

**Steps:**

1. Click in "Subject" field
2. Start typing
3. **Expected:** Counter appears below showing "X/100"

4. Click in "Message" field
5. Type some text
6. **Expected:** Counter shows "X/5000"

---

### Test 4: Real-Time Feedback

**Steps:**

1. Fill in Name: "J" (only 1 character)
2. Click outside
3. **Expected:** Error appears - "Name must be at least 2 characters"

4. Add one more character: "Jo"
5. **Expected:** Error disappears, field is valid (green border)

---

## 🔌 Connecting to Backend

### Check Backend is Running

In another terminal, verify the API is running:

```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{
  "status": "ok",
  "service": "fte-api",
  "ready": true
}
```

### Form Submission Flow

When you submit the form:

1. **Frontend** validates all fields locally
2. **Frontend** sends POST request to: `http://localhost:8000/api/messages/submit`
3. **Backend** receives and validates data
4. **Backend** publishes to Kafka
5. **Backend** returns Ticket ID
6. **Frontend** displays success message with Ticket ID

---

## 📱 Responsive Design Testing

### Test on Different Screen Sizes

**Desktop (1920x1080):**
```bash
# Chrome DevTools: F12 → Device Toolbar
# Select "Desktop"
# Expected: 2-column layout (Name/Email, Category/Priority)
```

**Tablet (768x1024):**
```bash
# Chrome DevTools: Device Toolbar
# Select "iPad"
# Expected: 2-column layout still visible
```

**Mobile (375x667):**
```bash
# Chrome DevTools: Device Toolbar
# Select "iPhone"
# Expected: Single column, full-width form
```

---

## 🎨 Customization (Optional)

### Change Colors

Edit: `production/web-form/SupportForm.tsx`

Find this section:
```tsx
<div className="bg-gradient-to-r from-blue-600 to-blue-700">
```

Change to:
```tsx
<div className="bg-gradient-to-r from-purple-600 to-purple-700">
```

### Change Form Title

Find:
```tsx
<h1 className="text-3xl font-bold text-white">Customer Support Form</h1>
```

Change to:
```tsx
<h1 className="text-3xl font-bold text-white">Help & Support</h1>
```

Save file → Browser automatically reloads

---

## ❌ Troubleshooting

### Issue: "npm command not found"
**Solution:**
- Node.js not installed
- Close and reopen terminal
- Run: `node --version` to verify

### Issue: Port 3000 already in use
**Solution:**
```bash
# Use different port
npm run dev -- -p 3001

# Then open: http://localhost:3001/web-form
```

### Issue: Form doesn't load
**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check browser console: F12 → Console tab
3. Look for red error messages
4. Refresh page: Ctrl+R

### Issue: Submit button doesn't work
**Solution:**
1. Open browser console: F12
2. Check for red error messages
3. Verify backend is running
4. Verify all required fields are filled
5. Check network tab for the POST request

### Issue: Getting CORS error
**Solution:**
The backend needs to allow requests from `localhost:3000`

Check `.env` file has:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

Restart FastAPI backend after changing

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Node.js installed (`node --version` shows version)
- [ ] npm installed (`npm --version` shows version)
- [ ] Web form dependencies installed (`npm install` completed)
- [ ] Backend API running (`curl http://localhost:8000/api/health` returns 200)
- [ ] Web form loads in browser (`http://localhost:3000/web-form`)
- [ ] Form displays all 7 fields
- [ ] Form validates input (try leaving fields empty)
- [ ] Submit button works (successful submission shows ticket ID)
- [ ] Responsive design works (test on mobile view)

---

## 📊 Next Steps

Once the web form is running:

1. **Test with Backend Integration**
   - See SETUP_GMAIL.md for email integration
   - See SETUP_WHATSAPP.md for WhatsApp integration

2. **Monitor Backend**
   - Watch FastAPI logs for incoming requests
   - Check database for saved messages
   - Verify Kafka publishes messages

3. **Load Testing**
   - Run: `locust -f production/tests/load_test.py --host=http://localhost:8000 -u 10 -r 2 -t 5m`
   - Submit multiple forms rapidly
   - Monitor system performance

4. **Production Deployment**
   - See `production/README.md` for deployment guide
   - Deploy to Vercel, Netlify, or Docker

---

## 📚 File Locations

**Web Form Files:**
- Component: `production/web-form/SupportForm.tsx`
- Page: `production/web-form/page.tsx`
- Layout: `production/web-form/layout.tsx`
- Config: `production/web-form/next.config.js`
- Styles: `production/web-form/tailwind.config.js`
- Dependencies: `production/web-form/package.json`

---

## 💡 Tips

- **Hot Reload:** Save file → browser automatically updates
- **Console Errors:** F12 → Console tab shows all errors
- **Network Requests:** F12 → Network tab shows API calls
- **Clear Cache:** Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
- **Kill Terminal:** Ctrl+C to stop development server

---

## 🎉 Success!

You've successfully:
- ✅ Setup Next.js web form
- ✅ Installed all dependencies
- ✅ Started development server
- ✅ Tested form submission
- ✅ Verified integration with backend

**Next:** Setup Gmail and WhatsApp integrations using the other guides!

---

**Questions?** Check the troubleshooting section above or see `production/README.md` for more help.

*Web Form Setup Complete!* 🚀
