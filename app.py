"""Entry point for github-companion."""
import sys

from commands.version import show_gc_version
from commands.status import show_gc_status
from commands.help import show_help
from commands.latest import show_gc_latest
     
def main():
    print("===============================")   
    print("Github Companion  v0.1.0")
    print("===============================") 
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
    "version": show_gc_version,
    "status": show_gc_status,
    "latest": show_gc_latest,
    "help": show_help,
}
    if command in commands:
        commands.get(command)()
    
    
    
    

if __name__ == "__main__":
    main()
