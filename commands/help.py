from rich import print
from utils.ui import info

def show_help():   
    print()
    info(" Available commands: ")
    print("═══════════════════════════════════════════")
    print("version   show installed Git version")
    print("status    show Git status")
    print("latest    show Latest commit")
    print("pushed    show committed  details")
    print("profile   show Profile details ")
    print("help      show what are the commands are available ")
    print()
    print("Type")
    print()
    print("python app.py <command> to run a command")
    print("═══════════════════════════════════════════")
    
     