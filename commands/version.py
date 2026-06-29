from services.git_service import get_git_version


def show_gc_version():
    print()
    print("════════════════════════════════════")
    version = get_git_version()
    print("Git Version:")
    print()
    print(version)
    print("════════════════════════════════════")