#  features/auth/auth.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from utils.config import load_config, save_config, hash_passkey, PASSKEY_CONFIG_FILE, DEFAULT_PASSKEY

console = Console()

def initialize_passkey():
    """Initialize passkey configuration"""
    config = load_config(PASSKEY_CONFIG_FILE)
    if not config:
        passkey_hash = hash_passkey(DEFAULT_PASSKEY)
        new_config = {"passkey_hash": passkey_hash, "initialized": True}
        if save_config(PASSKEY_CONFIG_FILE, new_config):
            console.print(Panel(Text("🔐 Default passkey set: 'admin123'", style="bold yellow")))
            console.print(Panel(Text("⚠️  Change default passkey for security!", style="bold red")))

def verify_passkey():
    """Verify user passkey"""
    config = load_config(PASSKEY_CONFIG_FILE)
    if not config:
        console.print(Panel(Text("❌ Security configuration missing!", style="bold red")))
        return False

    stored_hash = config.get("passkey_hash")
    if not stored_hash:
        console.print(Panel(Text("❌ Invalid security configuration!", style="bold red")))
        return False

    console.print(Panel(Text("🔐 Authentication Required", style="bold blue")))
    
    attempts = 3
    while attempts > 0:
        from cli_app import safe_ask
        import questionary
        
        entered_passkey = safe_ask(questionary.password, "Enter passkey:")
        if not entered_passkey:
            console.print(Panel(Text("❌ Passkey cannot be empty!", style="bold red")))
            attempts -= 1
            continue
        
        if hash_passkey(entered_passkey) == stored_hash:
            console.print(Panel(Text("✅ Authentication successful!", style="bold green")))
            return True
        else:
            attempts -= 1
            if attempts > 0:
                console.print(Panel(Text(f"❌ Invalid passkey! {attempts} attempts left.", style="bold red")))
            else:
                console.print(Panel(Text("❌ Access denied! Contact support.", style="bold red")))
                return False
    
    return False

def change_passkey():
    """Change passkey with verification"""
    if not verify_passkey():
        return False
    
    console.print(Panel(Text("🔐 Change Passkey", style="bold blue")))
    
    from cli_app import safe_ask
    import questionary
    
    new_passkey = safe_ask(questionary.password, "Enter new passkey:")
    if not new_passkey:
        console.print(Panel(Text("❌ Passkey cannot be empty!", style="bold red")))
        return False
    
    confirm_passkey = safe_ask(questionary.password, "Confirm new passkey:")
    if new_passkey != confirm_passkey:
        console.print(Panel(Text("❌ Passkeys do not match!", style="bold red")))
        return False
    
    new_config = {"passkey_hash": hash_passkey(new_passkey), "initialized": True}
    if save_config(PASSKEY_CONFIG_FILE, new_config):
        console.print(Panel(Text("✅ Passkey changed!", style="bold green")))
        return True
    
    console.print(Panel(Text("❌ Failed to change passkey!", style="bold red")))
    return False