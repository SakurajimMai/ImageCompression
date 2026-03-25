# Image Compression App - Mac/iOS Style Minimalist UI Design

## Overview
This design document outlines the transformation of the PySide6 Image Compression application from a traditional boxed layout to a modern, minimalist macOS/iOS "Acrylic/Mica" style. The goal is to provide a clean, atmospheric, and highly professional user experience.

## Core Design Principles
1.  **Structure**: Completely remove the traditional `QGroupBox` with embedded borders. Replace it with a "Label + Card" layout (a standalone bold `QLabel` for the section title, followed by a frameless `QWidget` acting as the content container).
2.  **Shapes**: Emphasize soft lines with large rounded corners (`border-radius: 12px` for cards, `6px` to `8px` for inputs and buttons).
3.  **Borders & Shadow**: Remove all hard `1px solid` wireframe borders. Rely solely on background color contrast to differentiate visual hierarchy (App Background vs. Card Background).
4.  **Spacing & Typography**: Substantially increase margins and paddings to create "breathing room" (36px minimum height for interactive elements). Use thicker fonts for titles (`font-weight: 600`) and lighter fonts for hints. 
5.  **Navigation**: Transform the `QTabWidget` into a modern, frameless segmented-control style navigation bar.

## Color Palette (QSS Implementation)

*   **Light Theme**:
    *   Window Background: `#F2F2F7` (macOS Light Gray)
    *   Card Background: `#FFFFFF` (Pure White)
    *   Text (Primary/Secondary): `#1C1C1E` / `#8E8E93`
    *   Accent (Buttons/Active Tabs): `#007AFF` (Apple Blue)

*   **Dark Theme**:
    *   Window Background: `#000000` or `#1C1C1E` (Deep Dark)
    *   Card Background: `#1C1C1E` or `#2C2C2E` (Elevated Gray)
    *   Text (Primary/Secondary): `#FFFFFF` / `#EBEBF5 alpha 60%`
    *   Accent (Buttons/Active Tabs): `#0A84FF` (Apple Light Blue)

*   **Gray Theme (Pro/Neutral)**:
    *   Window Background: `#0F172A` (Slate 900)
    *   Card Background: `#1E293B` (Slate 800)
    *   Text: `#F8FAFC` / `#94A3B8`
    *   Accent: `#38BDF8` (Sky)

## Implementation Details
1.  **Refactor `ui/theme.py`**: Rewrite the QSS styles for `QMainWindow`, `QWidget#card`, `QTabWidget`, `QLineEdit`, `QPushButton`, and `QComboBox`.
2.  **Component Upgrades**:
    *   Replace `QGroupBox("Title")` instantiations in all 5 tabs (`PrepareTab`, `CompressTab`, `UploadTab`, `SettingsTab`, `HelpTab`) with a custom UI builder pattern: `QLabel("Title")` + `QWidget(objectName="card")`.
3.  **Layout Adjustments**:
    *   Adjust `QVBoxLayout` and `QHBoxLayout` spacings to accommodate the new card-based padding rules.
    *   Ensure the bottom `ProgressWidget` and `UrlOutputWidget` blend seamlessly into the new frameless environment.
