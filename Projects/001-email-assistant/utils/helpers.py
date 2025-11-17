# utils/config.py
import re
import textwrap
from datetime import datetime
from email.utils import parsedate_to_datetime

def clean_email_body(body):
    """Clean HTML and format email body"""
    if not body:
        return "(No content)"
    
    clean_body = re.sub(r'<[^>]+>', '', body)
    clean_body = re.sub(r'\s+', ' ', clean_body)
    return clean_body.strip()

def format_email_date(date_string):
    """Format email date in readable format"""
    if not date_string:
        return "Unknown date"
    
    try:
        dt = parsedate_to_datetime(date_string)
        now = datetime.now()
        
        if dt.date() == now.date():
            return f"Today at {dt.strftime('%I:%M %p')}"
        elif dt.date() == now.replace(day=now.day-1).date():
            return f"Yesterday at {dt.strftime('%I:%M %p')}"
        else:
            return dt.strftime("%b %d, %Y at %I:%M %p")
    except:
        return date_string[:25]

def extract_clean_sender(sender_header):
    """Extract clean sender name and email"""
    if not sender_header:
        return "Unknown Sender"
    
    match = re.match(r'(.*?)<([^>]+)>', sender_header)
    if match:
        name = match.group(1).strip().strip('"')
        email = match.group(2).strip()
        return f"{name} <{email}>" if name else email
    
    return sender_header

def wrap_text(text, width=70):
    """Wrap text to specified width"""
    return textwrap.fill(text, width=width)