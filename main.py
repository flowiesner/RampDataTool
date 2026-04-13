"""
Ramp Data Collection Tool — entry point.
"""

from app.database   import init_db
from app.app_window import App

if __name__ == "__main__":
    init_db()
    App().mainloop()
