from rich import print

def header():
    banner = r"""
 ██████╗  ██████╗
██╔════╝ ██╔════╝
██║  ███╗██║
██║   ██║██║
╚██████╔╝╚██████╗
 ╚═════╝ ╚═════╝
    """

    print(f"[blue]{banner}[/blue]")
    print("[bold white]GitHub Companion[/bold white]")
    print("[dim]Developer CLI • v0.1.1[/dim]")
    print("[blue]" + "─" * 42 + "[/blue]")



def success(message):
    print(f"[bold green]✅ {message}[/bold green]")   
    
def warning(message):
    print(f"[bold yellow]⚠️ {message}[/bold yellow]")


def error(message):
    print(f"[bold red]❌ {message}[/bold red]")

def info(message):
    print(f"[bold cyan]ℹ️ {message}[/bold cyan]")