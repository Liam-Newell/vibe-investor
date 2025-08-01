#!/usr/bin/env python3
"""
Quick Email Test - Verify Email Notifications Are Working
"""

import asyncio
import logging
from src.services.email_service import EmailService
from src.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_notifications():
    """Test that email notifications are working"""
    
    print("📧 TESTING EMAIL NOTIFICATIONS")
    print("=" * 40)
    
    # Check config
    print(f"📋 Email Configuration:")
    print(f"   EMAIL_ENABLED: {settings.EMAIL_ENABLED}")
    print(f"   SMTP_SERVER: {settings.SMTP_SERVER}")
    print(f"   SMTP_PORT: {settings.SMTP_PORT}")
    print(f"   EMAIL_USERNAME: {settings.EMAIL_USERNAME}")
    print(f"   EMAIL_PASSWORD: {'***SET***' if settings.EMAIL_PASSWORD else 'NOT SET'}")
    print()
    
    if not settings.EMAIL_ENABLED:
        print("❌ EMAIL NOTIFICATIONS DISABLED!")
        print("   Fix: Set EMAIL_ENABLED = True in src/core/config.py")
        return False
    
    if not settings.EMAIL_PASSWORD:
        print("❌ EMAIL PASSWORD NOT SET!")
        print("   Fix: Set EMAIL_PASSWORD in environment variables")
        return False
    
    try:
        # Initialize email service
        email_service = EmailService()
        
        # Test simple email
        print("📧 Sending test email...")
        
        success = await email_service._send_email(
            to_email="liam-newell@hotmail.com",
            subject="🧪 Vibe Investor Email Test",
            html_content="""
            <h2>✅ Email Test Successful!</h2>
            <p>This confirms that email notifications are working properly.</p>
            <p><strong>Time:</strong> {}</p>
            <p><strong>Status:</strong> Email system operational</p>
            """.format(asyncio.get_event_loop().time())
        )
        
        if success:
            print("✅ EMAIL TEST SUCCESSFUL!")
            print("   Check your inbox for the test email")
            return True
        else:
            print("❌ EMAIL TEST FAILED!")
            print("   Check SMTP settings and credentials")
            return False
            
    except Exception as e:
        print(f"❌ EMAIL TEST ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_email_notifications()) 