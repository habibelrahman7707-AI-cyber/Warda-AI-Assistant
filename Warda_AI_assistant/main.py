import os
import sys

# Ensure root directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Warda AI Native Desktop App...")
    from ui.desktop_app import DesktopApp
    app = DesktopApp()
    app.mainloop()
