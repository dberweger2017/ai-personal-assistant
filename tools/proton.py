from protonmail import ProtonMail
from bs4 import BeautifulSoup
from datetime import datetime as dt
from typing import List
import os

session_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret", "protonmail_session.pkl")

if not os.path.exists(os.path.dirname(session_file_path)):
    os.makedirs(os.path.dirname(session_file_path))

proton = ProtonMail()

def session_exists_and_is_valid():
    if os.path.exists(session_file_path):
        try:
            proton.load_session(session_file_path)
            proton.get_user_info()
            return True
        except Exception as e:
            print(f"Session is invalid or expired: {e}")
    return False

if not session_exists_and_is_valid():
    username = "dberweger2017@proton.me"
    password = "ZurichBarcelona1318!2024"
    proton.login(username, password)
    proton.save_session(session_file_path)

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text(separator=" ")
    clean_text = " ".join(text.split())
    return clean_text

def get_emails_pure(n, search_keyword, only_unread):
    print(f"Getting {n} emails with keyword {search_keyword} ({only_unread})")
    try:
        messages = proton.get_messages()[:n]
        if only_unread:
            messages = [message for message in messages if message.unread]
        
        messages = [proton.read_message(message) for message in messages]
        
        if search_keyword:
            messages = [
                message for message in messages 
                if search_keyword.lower() in message.subject.lower() or search_keyword.lower() in message.body.lower() or search_keyword.lower() in message.sender.address.lower()
            ]

        return {
            'emails': [{
                'from': message.sender.address,
                'to': [recipient.address for recipient in message.recipients],
                'subject': message.subject,
                'body': clean_html(message.body),
                'time': dt.fromtimestamp(message.time).strftime('%Y-%m-%d %H:%M:%S'),
                'id': message.id
            } for message in messages]
        }
    except Exception as e:
        return {'error': str(e)}   
     
def send_email_pure(recipients: List[str], subject: str, html: str):
    print(f"Sending email to {recipients} with subject {subject}")
    try:
        new_message = proton.create_message(
            recipients=recipients,
            subject=subject,
            body=html,
        )
        proton.send_message(new_message)
    except Exception as e:
        print(f"Error sending email: {e}")
        return {'success': False, 'message': str(e)}
    return {'success': True, 'message': 'Email sent successfully'}

def delete_email_pure(email_ids: List[str]):
    print(f"Deleting emails: {email_ids}")
    try:
        proton.delete_messages(email_ids)
    except Exception as e:
        print(f"Error deleting emails: {e}")
        return {'success': False, 'message': str(e)}
    return {'success': True, 'message': f"Deleted {len(email_ids)} emails"}