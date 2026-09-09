# Desktop Chat Client (Linux & Windows) - Specification & Roadmap

> [!NOTE]
> **Status**: **ON HOLD**  
> This specification documents the planned architecture, technology stack, and UI flow for the desktop chat client (`expense-helper/desktop`). No code or implementation files are currently being generated for desktop. It is preserved here for future development.

---

## 1. Overview

The desktop companion for `expense-helper` is planned as a high-performance, lightweight, cross-platform native client targeting **Linux** and **Windows**.

- **Framework**: [Iced](https://github.com/iced-rs/iced) (Rust native GUI framework)
- **Target OS**:
  - Linux (X11 & Wayland via `winit` / `wgpu`)
  - Windows 10/11 (DirectX / Vulkan / Software rendering fallback)
- **Binary Footprint**: ~15–25 MB standalone native executable (zero runtime dependency on Electron, Node, or WebKit).

---

## 2. Technical Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Rust (2021 edition) | Memory safety, speed, and cross-platform native compilation. |
| **GUI Framework** | `iced` (0.12 or 0.13) | Declarative, Elm-inspired GUI architecture (`Message` -> `update` -> `view`). |
| **Async Runtime** | `tokio` | Asynchronous I/O execution. |
| **Networking** | `reqwest` + `serde` / `serde_json` | HTTP client communicating with `aimodel` (port `8001`). |

---

## 3. UI/UX Specification

### Layout
- **Window Size**: 480x720 (minimum), resizable.
- **Header**:
  - App title: `Expense Helper`
  - Connection indicator (Green dot for backend connected, Red dot for disconnected).
- **Chat Timeline**:
  - Scrollable container of message bubbles:
    - **User Messages**: Right-aligned, primary accent background.
    - **Assistant Messages**: Left-aligned, dark surface card background.
- **Interactive Action Cards**:
  - When the assistant extracts an expense draft (`AWAITING_CONFIRMATION`), render an action box inside the assistant bubble:
    - Extracted fields: Description, Amount, Category, Date.
    - Action buttons:
      - `[Confirm & Save to DB]` (Sends confirmation to `/api/chat/confirm`).
      - `[Discard / Cancel]` (Sends cancellation to `/api/chat/cancel`).
- **Footer**:
  - Text input field supporting multiline / single-line input.
  - Send button or `Enter` shortcut to submit.

---

## 4. Planned Project Structure (When Resumed)

```text
expense-helper/
└── desktop/
    ├── Cargo.toml
    ├── src/
    │   ├── main.rs              # Iced application entry point & event loop
    │   ├── types.rs             # Message models, ExpenseDraft, ChatMessage
    │   ├── api.rs               # Reqwest client calls to aimodel
    │   ├── state.rs             # State management & messages (enum Message)
    │   └── ui/
    │       ├── message_bubble.rs # Chat bubble renderer
    │       └── draft_card.rs     # Action card with confirm/cancel buttons
```

---

## 5. Build & Packaging Roadmap

### Linux (x86_64)
```bash
cargo build --release
# Outputs native binary target/release/expense-helper-desktop
```

### Windows (x86_64)
Cross-compilation from Linux via `mingw-w64`:
```bash
cargo build --target x86_64-pc-windows-gnu --release
```
Or native compilation in MSVC environment.
