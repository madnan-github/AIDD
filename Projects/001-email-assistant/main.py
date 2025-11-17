# main.py
import questionary
import imaplib
import smtplib
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import modular features
try:
    from features.email_reader.email_reader import fetch_emails
    from features.email_replier.email_replier import interactive_reply
    from features.auth.auth import initialize_passkey, verify_passkey, change_passkey
    from utils.config import load_config, save_config, EMAIL_CONFIG_FILE
    from utils.helpers import clean_email_body, format_email_date, extract_clean_sender, wrap_text
except ImportError:
    # For PyInstaller bundled executable
    from email_reader import fetch_emails
    from email_replier import interactive_reply
    from auth import initialize_passkey, verify_passkey, change_passkey
    from config import load_config, save_config, EMAIL_CONFIG_FILE
    from helpers import clean_email_body, format_email_date, extract_clean_sender, wrap_text

console = Console()

def safe_ask(question_func, *args, **kwargs):
    """Safely ask questions with PyInstaller compatibility"""
    try:
        return question_func(*args, **kwargs).ask()
    except (EOFError, KeyboardInterrupt):
        console.print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return None

def configure_email():
    """Configure email settings (requires passkey authentication)"""
    if not verify_passkey():
        console.print(Panel(Text("🚫 Access to email configuration denied!", style="bold red")))
        return

    console.print(Panel(Text("Email Configuration", justify="center", style="bold blue")))
    current_config = load_config(EMAIL_CONFIG_FILE)

    config_data = {
        "email_address": safe_ask(questionary.text, "Enter your email address:", 
                                 default=str(current_config.get("email_address", ""))),
        "imap_server": safe_ask(questionary.text, "Enter your IMAP server:", 
                               default=str(current_config.get("imap_server", "imap.gmail.com"))),
        "imap_port": safe_ask(questionary.text, "Enter your IMAP port:", 
                             default=str(current_config.get("imap_port", "993"))),
        "smtp_server": safe_ask(questionary.text, "Enter your SMTP server:", 
                               default=str(current_config.get("smtp_server", "smtp.gmail.com"))),
        "smtp_port": safe_ask(questionary.text, "Enter your SMTP port:", 
                             default=str(current_config.get("smtp_port", "587"))),
        "app_password": safe_ask(questionary.password, "Enter your app password:", 
                                default=str(current_config.get("app_password", "")))
    }

    if any(value is None for value in config_data.values()):
        console.print(Panel(Text("Configuration cancelled.", style="bold yellow")))
        return

    if save_config(EMAIL_CONFIG_FILE, config_data):
        console.print(Panel(Text("✅ Email configuration saved!", style="bold green")))
    else:
        console.print(Panel(Text("❌ Failed to save configuration.", style="bold red")))

def connect_imap():
    """Connect to IMAP server"""
    config = load_config(EMAIL_CONFIG_FILE)
    required_fields = ["email_address", "app_password", "imap_server", "imap_port"]
    
    if not config or not all(config.get(field) for field in required_fields):
        console.print(Panel(Text("❌ Incomplete email configuration.", style="bold yellow")))
        return None

    try:
        mail = imaplib.IMAP4_SSL(config["imap_server"], int(config["imap_port"]))
        mail.login(config["email_address"], config["app_password"])
        console.print(Panel(Text("✅ IMAP connected!", style="bold green")))
        return mail
    except Exception as e:
        console.print(Panel(Text(f"❌ IMAP connection failed: {e}", style="bold red")))
        return None

def connect_smtp():
    """Connect to SMTP server"""
    config = load_config(EMAIL_CONFIG_FILE)
    required_fields = ["email_address", "app_password", "smtp_server", "smtp_port"]
    
    if not config or not all(config.get(field) for field in required_fields):
        console.print(Panel(Text("❌ Incomplete email configuration.", style="bold yellow")))
        return None

    try:
        server = smtplib.SMTP(config["smtp_server"], int(config["smtp_port"]))
        server.starttls()
        server.login(config["email_address"], config["app_password"])
        console.print(Panel(Text("✅ SMTP connected!", style="bold green")))
        return server
    except Exception as e:
        console.print(Panel(Text(f"❌ SMTP connection failed: {e}", style="bold red")))
        return None

def send_new_email(smtp_conn):
    """Send a new email"""
    config = load_config(EMAIL_CONFIG_FILE)
    sender_email = config.get("email_address")
    
    if not sender_email:
        console.print(Panel(Text("❌ Email not configured.", style="bold yellow")))
        return

    recipient = safe_ask(questionary.text, "To:")
    subject = safe_ask(questionary.text, "Subject:")
    body = safe_ask(questionary.text, "Message:")

    if not all([recipient, subject, body]):
        console.print(Panel(Text("❌ All fields required.", style="bold yellow")))
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        smtp_conn.send_message(msg)
        console.print(Panel(Text(f"✅ Sent to {recipient}!", style="bold green")))
    except Exception as e:
        console.print(Panel(Text(f"❌ Send failed: {e}", style="bold red")))

def view_email_details(email):
    """Display clean, formatted email details"""
    clean_sender = extract_clean_sender(email['sender'])
    clean_subject = email['subject'] or "(No Subject)"
    clean_date = format_email_date(email['date'])
    clean_body = clean_email_body(email['body'])
    
    console.print(Panel(Text("📧 Email Details", style="bold blue")))
    console.print(f"[bold]From:[/bold] {clean_sender}")
    console.print(f"[bold]Subject:[/bold] {clean_subject}")
    console.print(f"[bold]Date:[/bold] {clean_date}")
    console.print(f"\n[bold]Message:[/bold]")
    console.print("-" * 70)
    
    wrapped_text = wrap_text(clean_body, width=70)
    console.print(wrapped_text)
    console.print("-" * 70)

def display_emails_with_actions(emails):
    """Display emails with action options"""
    console.print(Panel(Text(f"📧 Found {len(emails)} emails", style="bold green")))
    
    for i, email in enumerate(emails, 1):
        clean_sender = extract_clean_sender(email['sender'])
        clean_date = format_email_date(email['date'])
        clean_preview = clean_email_body(email['body'])[:80] + "..." if len(clean_email_body(email['body'])) > 80 else clean_email_body(email['body'])
        
        console.print(f"\n[bold cyan]{i}.[/bold cyan]")
        console.print(f"   👤 From: {clean_sender}")
        console.print(f"   📝 Subject: {email['subject']}")
        console.print(f"   📅 Date: {clean_date}")
        console.print(f"   📄 Preview: {clean_preview}")
        console.print("-" * 70)

def handle_fetch_emails(imap_conn, smtp_conn):
    """Fetch emails and provide interactive options"""
    fetched_emails, error = fetch_emails(imap_conn, num_emails=10)
    
    if error:
        console.print(Panel(Text(f"❌ Error: {error}", style="bold red")))
        return
    elif not fetched_emails:
        console.print(Panel(Text("📭 No emails found.", style="bold yellow")))
        return

    display_emails_with_actions(fetched_emails)

    while True:
        action = safe_ask(
            questionary.select,
            "What would you like to do?",
            choices=[
                f"📨 Reply to email (1-{len(fetched_emails)})",
                f"👁️ View email details (1-{len(fetched_emails)})", 
                "🔄 Refresh email list",
                "↩️ Back to main menu"
            ]
        )

        if not action:
            break
            
        if action == "↩️ Back to main menu":
            break
        elif action == "🔄 Refresh email list":
            fetched_emails, error = fetch_emails(imap_conn, num_emails=10)
            if error:
                console.print(Panel(Text(f"❌ Error: {error}", style="bold red")))
            elif fetched_emails:
                display_emails_with_actions(fetched_emails)
            else:
                console.print(Panel(Text("📭 No emails.", style="bold yellow")))
        elif "Reply to email" in action:
            handle_reply_action(fetched_emails, smtp_conn)
        elif "View email details" in action:
            handle_view_action(fetched_emails)

def handle_reply_action(emails, smtp_conn):
    """Handle email reply action"""
    try:
        email_num = safe_ask(questionary.text, f"Enter email number to reply (1-{len(emails)}):")
        
        if not email_num:
            return
            
        index = int(email_num) - 1
        if 0 <= index < len(emails):
            sender_email = load_config(EMAIL_CONFIG_FILE).get("email_address")
            interactive_reply(smtp_conn, emails[index], sender_email)
        else:
            console.print(Panel(Text("❌ Invalid email number.", style="bold red")))
            
    except ValueError:
        console.print(Panel(Text("❌ Please enter a valid number.", style="bold red")))

def handle_view_action(emails):
    """Handle email view action"""
    try:
        email_num = safe_ask(questionary.text, f"Enter email number to view (1-{len(emails)}):")
        
        if not email_num:
            return
            
        index = int(email_num) - 1
        if 0 <= index < len(emails):
            view_email_details(emails[index])
        else:
            console.print(Panel(Text("❌ Invalid email number.", style="bold red")))
            
    except ValueError:
        console.print(Panel(Text("❌ Please enter a valid number.", style="bold red")))

def email_operations_loop(imap_conn, smtp_conn):
    """Main email operations loop"""
    while True:
        action = safe_ask(
            questionary.select,
            "Email Operations:",
            choices=[
                "📨 Fetch Emails", 
                "✉️ Send New Email", 
                "🔌 Disconnect"
            ]
        )

        if not action:
            break
            
        if action == "📨 Fetch Emails":
            handle_fetch_emails(imap_conn, smtp_conn)
        elif action == "✉️ Send New Email":
            send_new_email(smtp_conn)
        elif action == "🔌 Disconnect":
            try:
                imap_conn.logout()
                smtp_conn.quit()
            except:
                pass
            console.print(Panel(Text("🔌 Disconnected.", style="bold green")))
            break

def main():
    """Main function with error handling"""
    try:
        # Initialize passkey system
        initialize_passkey()
        
        console.print(Panel(Text("📧 Secure Email Client", justify="center", style="bold green")))
        
        while True:
            action = safe_ask(
                questionary.select,
                "Main Menu:",
                choices=[
                    "⚙️ Configure Email", 
                    "🔐 Change Passkey",
                    "📥 Connect to Inbox", 
                    "🚪 Exit"
                ]
            )

            if not action:
                break
                
            if action == "⚙️ Configure Email":
                configure_email()
            elif action == "🔐 Change Passkey":
                change_passkey()
            elif action == "📥 Connect to Inbox":
                imap_conn = connect_imap()
                smtp_conn = connect_smtp()
                if imap_conn and smtp_conn:
                    email_operations_loop(imap_conn, smtp_conn)
            elif action == "🚪 Exit":
                console.print(Panel(Text("👋 Goodbye!", style="bold red")))
                break
                
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        console.print("Please report this issue.")

if __name__ == "__main__":
    main()