# features/email_replier/email_replier.py
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def interactive_reply(smtp_conn, original_email, sender_email):
    """Interactive email reply"""
    console.print(Panel(Text("Reply to Email", style="bold blue")))
    
    console.print(f"[bold]From:[/bold] {original_email['sender']}")
    console.print(f"[bold]Subject:[/bold] {original_email['subject']}")
    console.print(f"[bold]Preview:[/bold] {original_email['body'][:200]}...")
    console.print("\n" + "="*50)
    
    reply_body = console.input("\n[bold green]Your reply:[/bold green]\n")
    
    if not reply_body.strip():
        console.print(Panel(Text("Empty reply.", style="bold yellow")))
        return False
    
    success, error = send_reply(smtp_conn, original_email, reply_body, sender_email)
    
    if success:
        console.print(Panel(Text("Reply sent!", style="bold green")))
        return True
    else:
        console.print(Panel(Text(f"Send failed: {error}", style="bold red")))
        return False

def send_reply(smtp_conn, original_email, reply_body, sender_email):
    """Send email reply"""
    try:
        msg = MIMEMultipart()
        original_sender = extract_email(original_email['sender'])
        
        msg['From'] = sender_email
        msg['To'] = original_sender
        msg['Subject'] = f"Re: {original_email['subject']}"
        
        if 'raw_message' in original_email and 'Message-ID' in original_email['raw_message']:
            msg_id = original_email['raw_message']['Message-ID']
            msg['In-Reply-To'] = msg_id
            msg['References'] = msg_id
        
        formatted_body = format_reply(reply_body, original_email)
        msg.attach(MIMEText(formatted_body, 'plain'))
        
        smtp_conn.send_message(msg)
        return True, None
        
    except Exception as e:
        return False, str(e)

def format_reply(reply_body, original_email):
    """Format reply with original message"""
    formatted = f"{reply_body}\n\n"
    formatted += f"> On {original_email['date']}, {original_email['sender']} wrote:\n"
    formatted += "> " + original_email['body'][:300].replace('\n', '\n> ')
    return formatted

def extract_email(header):
    """Extract email address from header"""
    match = re.search(r'<([^>]+)>', header)
    if match:
        return match.group(1)
    
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', header)
    return match.group(0) if match else header