import os
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_with_code(user_email, code):
    if not user_email or not user_email.strip():
        return  # email opzionale

    base_url = os.environ.get('CRAB_BASE_URL', 'https://crab.bio.uniroma2.it')
    link_results = f'{base_url}/waiting?uid={code}'
    mail_content = (
        "Dear CRAB user,\n"
        "you can find the result of your research at the following link:\n\n"
        f"{link_results}\n\n\nBest regards,\nCRAB Team"
    )

    sender_address = os.environ.get('CRAB_SMTP_USER', '')
    sender_pass = os.environ.get('CRAB_SMTP_PASSWORD', '')
    if not sender_address or not sender_pass:
        print('Email disabled: CRAB_SMTP_USER / CRAB_SMTP_PASSWORD not set')
        return
    receiver_address = user_email.strip()

    message = MIMEMultipart()
    message['From'] = f"CRAB Team <{sender_address}>"
    message['To'] = receiver_address
    message['Subject'] = 'CRAB Team: your results'
    message.attach(MIMEText(mail_content, 'plain'))

    try:
        # timeout per non farlo bloccare se la mail non funziona
        session = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        session.ehlo()
        session.starttls()
        session.ehlo()
        session.login(sender_address, sender_pass)
        session.sendmail(sender_address, receiver_address, message.as_string())
        session.quit()
        print('Mail Sent')
    except (smtplib.SMTPException, socket.timeout, OSError) as e:
        # NON bloccare tutta la pipeline se l'email non parte
        print(f'Email failed: {e}')

