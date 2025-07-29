# 📧 Quick Email Start (No Registration Needed!)

**Want to start receiving trading reports immediately? Use your existing email!**

## 🚀 5-Minute Setup with Gmail

### Step 1: Get Gmail App Password (2 minutes)
1. Go to https://myaccount.google.com/apppasswords
2. Select **"Mail"** and generate password
3. Copy the 16-character password (like `abcd efgh ijkl mnop`)

### Step 2: Configure Your System (1 minute)
Edit your `.env` file:

```bash
# Enable email
EMAIL_ENABLED=true

# Gmail SMTP (easiest option)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # Your app password

# Where to send reports
ALERT_EMAIL=liam-newell@hotmail.com
```

### Step 3: Test (30 seconds)
```bash
# Start your app
python main.py

# Send test email
curl -X POST http://localhost:8080/api/v1/email/test-morning-email
```

**Done!** Check your hotmail inbox for a beautiful trading report!

---

## 🎯 What You Get

**From**: Vibe Investor <your-email@gmail.com>  
**To**: liam-newell@hotmail.com  
**Subject**: 🌅 Vibe Investor Morning Report

✅ **Works immediately** - No domain registration  
✅ **Professional appearance** - "Vibe Investor" sender name  
✅ **Beautiful reports** - Claude-generated HTML emails  
✅ **Free** - Just uses your existing Gmail  

---

## 🔧 Other Email Providers

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password  # Regular password, no app password needed
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password  # Generate at account.yahoo.com
```

### Any Other Provider
Most email providers work with these settings:
```bash
SMTP_SERVER=smtp.your-provider.com
SMTP_PORT=587  # or 465
SMTP_USER=your-email@provider.com
SMTP_PASSWORD=your-password
```

---

## 💎 Want Professional Custom Domain?

**Current**: Reports from `your-email@gmail.com`  
**Professional**: Reports from `vibe@vibeinvestor.ca`

See [SIMPLE_EMAIL_SETUP.md](SIMPLE_EMAIL_SETUP.md) for custom domain setup (~$15/year).

---

## 🆘 Troubleshooting

### Gmail App Password Issues
- **Enable 2FA first** - Required for app passwords
- **Use app password** - Not your regular Gmail password
- **Remove spaces** - Copy password without spaces

### Emails Not Sending
- **Check credentials** - Test with your email client first
- **Check logs** - Look at `logs/vibe_investor.log`
- **Test connection** - Use telnet or online SMTP testers

### Emails Going to Spam
- **Use "Vibe Investor" name** - Already configured
- **Whitelist sender** - Add to contacts in your hotmail
- **Check content** - Avoid spam trigger words

---

## 🎉 That's It!

**No domain registration, no server setup, no monthly fees.**

Just use your existing email and start receiving beautiful AI-generated trading reports in minutes!

**Next**: Configure your Claude API key and start paper trading! 🚀 