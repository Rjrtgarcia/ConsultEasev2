# Central System UI Module

## PyQt Components
- `MainWindow`: Primary application window with dashboard layout
- `AuthDialog`: RFID authentication interface
- `AdminPanel`: Faculty management CRUD interface

## Dependencies
- PyQt6
- QDarkStyleSheet
- Firebase Admin SDK

```python
# Basic window setup
from PyQt6.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("ConsultEase Central System")
        self.setMinimumSize(1024, 768)
```

[Installation instructions...]