# 📧 Simple Custom Email Setup
## Send from `vibe@vibeinvestor.ca` to your existing Hotmail

**Perfect setup**: Your trading reports will be sent to your existing **liam-newell@hotmail.com** but will appear to come from the professional **vibe@vibeinvestor.ca** address!

## 🎯 What You Get

✅ **Keep your existing email** - No need to check a new inbox  
✅ **Professional sender** - Reports come from `vibe@vibeinvestor.ca`  
✅ **Only one email account to create** - Just the sending account  
✅ **Beautiful Claude-generated reports** delivered to your hotmail  

## 🚀 Quick Setup with Zoho Mail (FREE)

### Step 1: Get the Domain
Register `vibeinvestor.ca` at any domain registrar:
- **Namecheap**: ~$15/year
- **GoDaddy**: ~$20/year  
- **Cloudflare**: ~$10/year (cheapest)

### Step 2: Sign Up for Zoho Mail
1. Go to https://www.zoho.com/mail/
2. Click **"Get Started for Free"**
3. Choose **"Add your own domain"**
4. Enter `vibeinvestor.ca`

### Step 3: Verify Domain Ownership
Zoho will give you DNS records to add. In your domain registrar:

```dns
# TXT Record for verification
TXT  @  zb12345678=abcdef...  # (Zoho provides exact code)

# MX Records for email delivery
MX   @  mx.zoho.com       10
MX   @  mx2.zoho.com      20  
MX   @  mx3.zoho.com      50

# SPF Record (prevents spam)
TXT  @  "v=spf1 include:zoho.com ~all"
```

### Step 4: Create Email Account
1. **Create only one account**: `vibe@vibeinvestor.ca`
2. **Set a strong password** (you'll use this in your .env)
3. **Skip creating liam@vibeinvestor.ca** - not needed!

### Step 5: Configure Your Trading System
Edit your `.env` file:

```bash
# Enable email notifications
EMAIL_ENABLED=true

# Zoho SMTP settings
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587

# Your new sending account
SMTP_USER=vibe@vibeinvestor.ca
SMTP_PASSWORD=your-zoho-password

# Your existing hotmail (where you receive reports)
ALERT_EMAIL=liam-newell@hotmail.com
```

### Step 6: Test It Works!
```bash
# Start your application
python main.py

# Test morning report
curl -X POST http://localhost:8080/api/v1/email/test-morning-email

# Check your hotmail inbox!
```

## 💰 Cost Breakdown

- **Domain registration**: $10-20/year
- **Zoho Mail**: **FREE** for up to 5 users
- **Total annual cost**: $10-20 (just the domain!)

## 🎨 What Your Emails Will Look Like

**From**: vibe@vibeinvestor.ca  
**To**: liam-newell@hotmail.com  
**Subject**: 🌅 Vibe Investor Morning Report - 2024-01-29

Beautiful HTML email with:
- Portfolio snapshot and performance
- Claude's market analysis  
- Specific options opportunities
- Risk assessment and position sizing
- Professional financial report styling

## 🔧 Alternative Options

### If you want different domain providers:

**ProtonMail** (~$4/month):
```bash
SMTP_SERVER=127.0.0.1  # Via ProtonMail Bridge
SMTP_PORT=1025
SMTP_USER=vibe@vibeinvestor.ca
```

**Self-hosted** (~$5/month VPS):
```bash
SMTP_SERVER=mail.vibeinvestor.ca
SMTP_PORT=587  
SMTP_USER=vibe@vibeinvestor.ca
```

### If you want to save money:
1. **Use subdomain**: `vibe@mail.yourdomain.com` with existing domain
2. **Free domain**: Some providers offer free subdomains
3. **Shared hosting**: Many hosting providers include email

## 🆘 Troubleshooting

### DNS Not Propagating
- **Wait**: DNS changes take 24-48 hours globally
- **Check**: Use https://dnschecker.org/ to verify

### Zoho Not Receiving Verification
- **Double-check TXT record** exactly as provided
- **Remove quotes** if your DNS provider adds them automatically
- **Contact support** - Zoho has excellent free support

### Emails Going to Spam
Add these DNS records:
```dns
# DKIM (Zoho will provide the exact record)
TXT  zmail._domainkey  "v=DKIM1; k=rsa; p=MIGfMA0GCSq..."

# DMARC  
TXT  _dmarc  "v=DMARC1; p=quarantine; rua=mailto:vibe@vibeinvestor.ca"
```

### Test SMTP Connection
```bash
# Install telnet (Windows)
telnet smtp.zoho.com 587

# Should connect successfully
220 mx.zoho.com ESMTP ready
```

## 🏆 Why This Setup is Perfect

✅ **Familiar inbox** - Keep using your hotmail  
✅ **Professional image** - Emails from `vibe@vibeinvestor.ca`  
✅ **No server maintenance** - Zoho handles everything  
✅ **Free email service** - Only pay for domain  
✅ **Reliable delivery** - Enterprise-grade uptime  
✅ **Easy management** - Web interface for settings  

## 🚀 Next Steps

1. **Register `vibeinvestor.ca`** domain
2. **Sign up for Zoho Mail** (free)
3. **Add DNS records** for verification
4. **Create `vibe@vibeinvestor.ca`** account
5. **Update your `.env`** configuration
6. **Test with API endpoints**
7. **Enjoy professional trading reports!**

---

**Result**: Beautiful Claude-generated trading reports delivered to your existing hotmail from a professional `vibe@vibeinvestor.ca` address! 📧✨ 