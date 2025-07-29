# 📧 Custom Domain Email Setup Guide
## Setting up `@vibe-investor.ca` Email Domain

This guide shows you how to set up professional email for your trading system using `@vibe-investor.ca` domain with **free hosting** or **self-hosted** solutions.

## 🎯 Overview

Your system will send reports to: **liam-newell@hotmail.com**  
Your system will send from: **vibe@vibeinvestor.ca**

## 🌟 Option 1: Zoho Mail (FREE - Recommended)

**Best for beginners** - Free custom domain email with professional features.

### Step 1: Domain Setup
1. **Buy domain**: Register `vibeinvestor.ca` at any registrar (Namecheap, GoDaddy, etc.)
2. **Sign up at Zoho**: Go to https://www.zoho.com/mail/
3. **Add your domain**: Follow Zoho's domain verification process

### Step 2: DNS Configuration
Add these DNS records to your domain:

```dns
# MX Records (for receiving email)
MX  @  mx.zoho.com  10
MX  @  mx2.zoho.com  20
MX  @  mx3.zoho.com  50

# CNAME Record (for verification)
CNAME  zb12345678  zmverify.zoho.com  # (Zoho will provide the exact code)

# TXT Record (for SPF)
TXT  @  "v=spf1 include:zoho.com ~all"
```

### Step 3: Create Email Account
1. **Create sending account**:
   - `vibe@vibeinvestor.ca` (for sending reports to your hotmail)

### Step 4: Configure .env
```bash
EMAIL_ENABLED=true
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=vibe@vibeinvestor.ca
SMTP_PASSWORD=your-zoho-password
ALERT_EMAIL=liam-newell@hotmail.com
```

**✅ Cost**: FREE for up to 5 users  
**✅ Features**: 5GB storage, mobile apps, web interface  
**✅ Reliability**: Enterprise-grade uptime  

---

## 🔒 Option 2: ProtonMail (FREE Custom Domain)

**Best for privacy** - Swiss-based, encrypted email service.

### Step 1: Domain Setup
1. **Sign up**: Go to https://proton.me/mail
2. **Upgrade plan**: Custom domains require paid plan (~$4/month)
3. **Add domain**: Add `vibe-investor.ca` in settings

### Step 2: DNS Configuration
```dns
# MX Records
MX  @  mail.protonmail.ch  10
MX  @  mailsec.protonmail.ch  20

# TXT Records
TXT  @  "v=spf1 include:_spf.protonmail.ch mx ~all"
TXT  protonmail._domainkey  "v=DKIM1; k=rsa; p=[PROVIDED_BY_PROTON]"
```

### Step 3: Configure Bridge (Required for SMTP)
1. **Download ProtonMail Bridge**: https://proton.me/mail/bridge
2. **Install and login**
3. **Get bridge credentials** (different from web login)

### Step 4: Configure .env
```bash
EMAIL_ENABLED=true
SMTP_SERVER=127.0.0.1  # ProtonMail Bridge local server
SMTP_PORT=1025
SMTP_USER=alerts@vibe-investor.ca
SMTP_PASSWORD=your-bridge-password  # From Bridge app, not web password
ALERT_EMAIL=liam@vibe-investor.ca
```

**✅ Features**: End-to-end encryption, privacy-focused  
**❌ Cost**: ~$4/month for custom domain  
**⚠️ Complexity**: Requires Bridge software  

---

## 🏠 Option 3: Self-Hosted with Mail-in-a-Box (FREE)

**Best for full control** - Complete email server on your VPS.

### Step 1: VPS Setup
1. **Get VPS**: DigitalOcean, Linode, Vultr (~$5/month)
2. **Requirements**: Ubuntu 22.04, 1GB RAM minimum, static IP
3. **Domain**: Point `vibe-investor.ca` A record to your VPS IP

### Step 2: Install Mail-in-a-Box
```bash
# On your VPS (as root)
curl -s https://mailinabox.email/setup.sh | sudo bash
```

### Step 3: Complete Setup
1. **Web admin**: Go to `https://your-vps-ip/admin`
2. **Create accounts**:
   - `liam@vibe-investor.ca`
   - `alerts@vibe-investor.ca`
3. **DNS**: Follow the DNS instructions provided by Mail-in-a-Box

### Step 4: Configure .env
```bash
EMAIL_ENABLED=true
SMTP_SERVER=mail.vibe-investor.ca  # Your VPS domain
SMTP_PORT=587
SMTP_USER=alerts@vibe-investor.ca
SMTP_PASSWORD=your-mailbox-password
ALERT_EMAIL=liam@vibe-investor.ca
```

**✅ Cost**: VPS only (~$5/month)  
**✅ Control**: Full server control, unlimited accounts  
**❌ Complexity**: Server maintenance required  
**❌ Reliability**: You manage uptime and backups  

---

## 🐳 Option 4: Self-Hosted with Docker (Mailcow)

**Best for Docker users** - Professional email stack in containers.

### Step 1: VPS with Docker
```bash
# Install Docker and Docker Compose
curl -sSL https://get.docker.com/ | CHANNEL=stable sh
sudo systemctl enable --now docker
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Install Mailcow
```bash
cd /opt
sudo git clone https://github.com/mailcow/mailcow-dockerized
cd mailcow-dockerized
sudo ./generate_config.sh  # Enter vibe-investor.ca when prompted
sudo docker-compose pull
sudo docker-compose up -d
```

### Step 3: Configure Mailcow
1. **Web interface**: `https://vibe-investor.ca`
2. **Login**: admin / moohoo (change immediately!)
3. **Create mailboxes**:
   - `liam@vibe-investor.ca`
   - `alerts@vibe-investor.ca`

### Step 4: Configure .env
```bash
EMAIL_ENABLED=true
SMTP_SERVER=vibe-investor.ca
SMTP_PORT=587
SMTP_USER=alerts@vibe-investor.ca
SMTP_PASSWORD=your-mailcow-password
ALERT_EMAIL=liam@vibe-investor.ca
```

**✅ Features**: Web admin, antispam, webmail  
**✅ Docker**: Easy deployment and updates  
**❌ Resources**: Requires more RAM (2GB+)  

---

## 🛠️ Option 5: Simple VPS with Postfix

**Best for minimal setup** - Basic SMTP server only.

### Step 1: Ubuntu VPS Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Postfix
sudo apt install postfix mailutils -y
# Choose "Internet Site" and enter "vibe-investor.ca"

# Install Dovecot for authentication
sudo apt install dovecot-core dovecot-imapd dovecot-pop3d -y
```

### Step 2: Configure Postfix
```bash
# Edit main configuration
sudo nano /etc/postfix/main.cf

# Add these lines:
mydomain = vibe-investor.ca
myhostname = mail.vibe-investor.ca
myorigin = $mydomain
inet_interfaces = all
mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
home_mailbox = Maildir/

# Enable SMTP authentication
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes
smtpd_recipient_restrictions = permit_sasl_authenticated,permit_mynetworks,reject_unauth_destination
```

### Step 3: Configure Dovecot
```bash
# Edit Dovecot config
sudo nano /etc/dovecot/dovecot.conf

# Uncomment:
protocols = imap pop3 lmtp

# Edit auth config
sudo nano /etc/dovecot/conf.d/10-auth.conf

# Change:
disable_plaintext_auth = no
auth_mechanisms = plain login
```

### Step 4: Create Email Users
```bash
# Create system users for email accounts
sudo adduser --disabled-login alerts
sudo adduser --disabled-login liam

# Set email passwords
sudo passwd alerts
sudo passwd liam

# Restart services
sudo systemctl restart postfix dovecot
```

### Step 5: DNS Configuration
```dns
# A Record
A    mail    YOUR_VPS_IP

# MX Record  
MX   @       mail.vibe-investor.ca    10

# SPF Record
TXT  @       "v=spf1 mx ~all"
```

### Step 6: Configure .env
```bash
EMAIL_ENABLED=true
SMTP_SERVER=mail.vibe-investor.ca
SMTP_PORT=587
SMTP_USER=alerts
SMTP_PASSWORD=your-system-password
ALERT_EMAIL=liam@vibe-investor.ca
```

**✅ Cost**: VPS only (~$5/month)  
**✅ Minimal**: Simple setup, low resources  
**❌ Features**: Basic SMTP only, no web interface  
**❌ Security**: Manual SSL/security setup required  

---

## 🔐 SSL/TLS Setup (For Self-Hosted)

### Let's Encrypt (Free SSL)
```bash
# Install Certbot
sudo apt install certbot -y

# Get SSL certificate
sudo certbot certonly --standalone -d mail.vibe-investor.ca -d vibe-investor.ca

# Configure Postfix for TLS
sudo nano /etc/postfix/main.cf

# Add:
smtpd_tls_cert_file=/etc/letsencrypt/live/vibe-investor.ca/fullchain.pem
smtpd_tls_key_file=/etc/letsencrypt/live/vibe-investor.ca/privkey.pem
smtpd_use_tls=yes
smtpd_tls_security_level=encrypt
smtp_tls_security_level=encrypt

# Restart Postfix
sudo systemctl restart postfix
```

---

## 📧 Testing Your Setup

### Quick Test with MailHog (No Real Email Needed)
```bash
# Test with Docker (includes fake SMTP server)
docker-compose -f docker-compose.yml -f docker-compose.email-test.yml up -d --profile email-test

# Access MailHog web interface to see emails
# http://localhost:8025

# Test email sending
curl -X POST http://localhost:8080/api/v1/email/test-morning-email

# Check captured emails at: http://localhost:8025
```

### Test SMTP Connection
```bash
# Install swaks (SMTP testing tool)
sudo apt install swaks -y

# Test sending email
swaks --to liam@vibe-investor.ca \
      --from alerts@vibe-investor.ca \
      --server mail.vibe-investor.ca:587 \
      --auth LOGIN \
      --auth-user alerts@vibe-investor.ca \
      --auth-password your-password \
      --tls
```

### Test with Trading System
```bash
# Start your application
python main.py

# Test morning report
curl -X POST http://localhost:8080/api/v1/email/test-morning-email

# Check email configuration
curl http://localhost:8080/api/v1/email/email-config
```

---

## 🏆 Recommendation

**For most users**: Start with **Zoho Mail** (Option 1)
- ✅ **Free** and reliable
- ✅ **Easy setup** with good documentation  
- ✅ **Professional features** without complexity
- ✅ **No server maintenance** required

**For privacy**: Use **ProtonMail** (Option 2)
**For full control**: Use **Mail-in-a-Box** (Option 3)
**For Docker experts**: Use **Mailcow** (Option 4)

---

## 🆘 Troubleshooting

### Common Issues
1. **Port 25 blocked**: Many VPS providers block port 25. Use port 587 for submission.
2. **DNS propagation**: Wait 24-48 hours for DNS changes to propagate globally.
3. **Spam filters**: Configure SPF, DKIM, and DMARC records properly.
4. **Firewall**: Ensure ports 25, 587, 993, 995 are open.

### Log Files
```bash
# Check mail logs
sudo tail -f /var/log/mail.log

# Check Postfix queue
sudo postqueue -p

# Check Dovecot logs
sudo tail -f /var/log/dovecot.log
```

Ready to receive beautiful trading reports at **liam@vibe-investor.ca**! 📈📧 