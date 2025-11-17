# features/email_reader/email_reader.py
import email
from email.header import decode_header
import re

def fetch_emails(imap_conn, num_emails=10, folder="INBOX"):
    """Fetch emails with body text"""
    try:
        status, _ = imap_conn.select(folder)
        if status != "OK":
            return None, f"Cannot select folder: {folder}"

        status, messages = imap_conn.search(None, "ALL")
        if status != "OK":
            return None, "Search failed"

        email_ids = messages[0].split()
        latest_ids = email_ids[-num_emails:] if len(email_ids) > num_emails else email_ids
        
        emails_data = []
        for email_id in reversed(latest_ids):
            email_data = fetch_single_email(imap_conn, email_id)
            if email_data:
                emails_data.append(email_data)
        
        return emails_data, None
        
    except Exception as e:
        return None, f"Fetch error: {str(e)}"

def fetch_single_email(imap_conn, email_id):
    """Fetch single email details"""
    try:
        status, msg_data = imap_conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            return None

        msg = email.message_from_bytes(msg_data[0][1])
        
        return {
            "id": email_id.decode(),
            "sender": decode_header_value(msg["From"]),
            "subject": decode_header_value(msg["Subject"]) or "(No Subject)",
            "date": msg["Date"],
            "body": extract_email_body(msg),
            "raw_message": msg
        }
        
    except Exception:
        return None

def decode_header_value(header):
    """Decode email header value"""
    if not header:
        return ""
    
    decoded_parts = decode_header(header)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding or 'utf-8'))
        else:
            result.append(part)
    
    return ' '.join(result)

def extract_email_body(msg):
    """Extract text body from email"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition", "")):
                continue
                
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    continue
                    
        if not body:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        html_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        body = html_to_plain_text(html_text)
                        break
                    except:
                        continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except:
            body = msg.get_payload()
    
    return clean_email_content(body) if body else "(No body content)"

def html_to_plain_text(html):
    """Convert HTML to plain text"""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_email_content(text):
    """Clean email content by removing common clutter"""
    if not text:
        return ""
    
    lines = text.split('\n')
    clean_lines = [line for line in lines if not line.strip().startswith('>')]
    cleaned_text = '\n'.join(clean_lines)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    
    return cleaned_text.strip()