import smtplib

smtp_server = "smtp.gmail.com"
port = 465  
username = "justgradproject25@gmail.com"
password = ""  
from_addr = "justgradproject25@gmail.com"
to_addr = "laithsocials@gmail.com"  

message = """\
Subject: Test Email

This is a test email sent from a simple script.
"""

try:
    
    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(username, password)
        server.sendmail(from_addr, to_addr, message)
    print("Email sent successfully!")
except Exception as e:
    print("Failed to send email:", e)
