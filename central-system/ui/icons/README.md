# UI Icons

This directory contains icons used in the ConsultEase UI.

## Icon List

- `logo.png` - Main application logo
- `check.png` - Checkmark icon for checkboxes
- `down-arrow.png` - Down arrow for dropdown menus
- `user.png` - User icon
- `faculty.png` - Faculty icon
- `admin.png` - Admin icon
- `settings.png` - Settings icon
- `logout.png` - Logout icon
- `refresh.png` - Refresh icon

## Icon Credits

These icons should be replaced with actual icons before deployment. You can use icon sets like:

1. [Material Design Icons](https://materialdesignicons.com/)
2. [Font Awesome](https://fontawesome.com/)
3. [Feather Icons](https://feathericons.com/)

## Usage

Icons are referenced in the stylesheet and in the UI code. To use an icon:

```python
from PyQt6.QtGui import QIcon
icon = QIcon("ui/icons/icon_name.png")
```

Or in the stylesheet:

```css
QToolButton {
    image: url(icons/icon_name.png);
}