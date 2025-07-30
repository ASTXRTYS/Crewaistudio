# AUREN PWA Implementation Blueprint

*   **Created**: July 29, 2025
*   **Purpose**: To serve as the definitive technical guide for the AUREN PWA, detailing its architecture, components, and deployment process. This document captures the end-to-end setup from our session.

---

## 1. Core Architecture & Philosophy

The AUREN PWA is designed as a **decoupled frontend application** that communicates with the main AUREN backend infrastructure.

*   **Frontend**: A modern React application built with Vite for fast development and optimized builds. Hosted on **Vercel** for global CDN distribution, performance, and instant deployments.
*   **Backend**: The existing AUREN production environment running on **DigitalOcean** (`144.126.215.218`).
*   **Communication**: The PWA uses a dual-communication strategy:
    1.  **WebSocket (`ws://`)**: For real-time, bidirectional chat with NEUROS.
    2.  **REST API (`http://`)**: For initial data loading (chat history), file uploads, and as a reliable fallback if the WebSocket connection is unavailable.

---

## 2. Project Setup & Dependencies

The project was initialized and configured with the following steps.

### 2.1. Initial Scaffolding

The project is a standard **Vite + React** application.

```bash
# 1. Navigate to the desired parent directory
# Example: cd /Users/Jason/Downloads

# 2. Create the Vite project
npm create vite@latest auren-pwa -- --template react

# 3. Navigate into the new project directory
cd auren-pwa
```

### 2.2. Core Dependencies Installed

The following libraries form the foundation of the PWA:

```bash
npm install \
  zustand \                  # For simple, powerful global state management
  react-audio-voice-recorder \ # For voice message recording UI
  lucide-react \             # For sleek, modern icons
  clsx \                     # For conditional CSS class naming
  axios \                    # For making REST API calls to the backend
  vite-plugin-pwa \          # For PWA manifest and service worker generation
  workbox-window             # For service worker registration
```

---

## 3. Project Structure

The final project structure is organized for clarity and scalability.

```
auren-pwa/
├── .env.local                # Local environment variables (API/WS URLs)
├── index.html                # Main HTML entry point
├── package.json              # Project dependencies and scripts
├── vercel.json               # Vercel deployment configuration (proxies)
├── vite.config.js            # Vite build and PWA configuration
│
├── public/
│   ├── manifest.json         # PWA manifest file
│   └── icons/                # App icons for different devices
│
└── src/
    ├── App.css               # Main application layout styles
    ├── App.jsx               # Root React component
    ├── index.css             # Global styles and CSS variables
    ├── main.jsx              # React application entry point
    ├── store.js              # Zustand global state store
    │
    ├── components/           # Reusable UI components
    │   ├── ChatWindow.jsx
    │   ├── InputBar.jsx
    │   └── MessageBubble.jsx
    │
    ├── hooks/                # Custom React hooks
    │   └── useWebSocket.js
    │
    └── utils/                # Utility functions
        └── api.js
```

---

## 4. Component Breakdown

### `App.jsx`
*   **Role**: The main application component.
*   **Responsibilities**:
    *   Renders the primary layout (Header, Chat Container).
    *   Initializes the WebSocket connection via the `useWebSocket` hook.
    *   Handles sending messages from the `InputBar` to the backend.
    *   Fetches initial chat history.

### `ChatWindow.jsx`
*   **Role**: Displays the conversation.
*   **Responsibilities**:
    *   Subscribes to the `messages` array in the Zustand store.
    *   Renders an empty state if there are no messages.
    *   Maps over the messages and renders a `MessageBubble` for each one.
    *   Automatically scrolls to the bottom when new messages are added.

### `MessageBubble.jsx`
*   **Role**: Displays a single chat message.
*   **Responsibilities**:
    *   Applies different styling based on the message `sender` (`user`, `agent`, or `system`).
    *   Formats and displays the message text and timestamp.

### `InputBar.jsx`
*   **Role**: The user input area for chat.
*   **Responsibilities**:
    *   Manages the text input field.
    *   Provides buttons for sending text, uploading files, and recording voice.
    *   Calls the appropriate API functions for voice/file uploads.
    *   Passes the user's text message up to `App.jsx` to be sent.

---

## 5. State & Data Flow

### 5.1. State Management (`store.js`)
We use **Zustand** for a lightweight global store.
*   **`messages`**: An array holding all chat messages for the current session.
*   **`connectionStatus`**: A string (`'connecting'`, `'connected'`, `'disconnected'`) tracking the WebSocket status.
*   **`sessionId`**: A unique ID for the current chat session, used for API calls and WebSocket communication.

### 5.2. Backend Communication
*   **`utils/api.js`**: Contains all `axios`-based functions for communicating with the REST API endpoints on the backend. This handles text, voice, files, and history.
*   **`hooks/useWebSocket.js`**: A custom hook that manages the entire WebSocket lifecycle, including connection, reconnection, message sending, and receiving.

---

## 6. PWA & Deployment

### 6.1. PWA Configuration (`vite.config.js`)
The `vite-plugin-pwa` automatically generates the `manifest.json` and a service worker (`sw.js`) during the build process. This enables:
*   **Installability**: Users can "Add to Home Screen" for a native-app feel.
*   **Offline Support**: The service worker provides basic offline capabilities (though real-time chat requires a connection).

### 6.2. Deployment to Vercel
The PWA is deployed from the local machine using the Vercel CLI.

**Deployment Steps:**
1.  Install the Vercel CLI: `npm i -g vercel`
2.  Log in to Vercel: `vercel login`
3.  From the `auren-pwa/` directory, deploy to production: `vercel --prod`

### 6.3. Vercel Proxy (`vercel.json`)
To avoid CORS issues and securely connect to the backend, `vercel.json` is configured to act as a reverse proxy.
*   Requests from the PWA to `/api/...` are rewritten to `http://144.126.215.218:8888/api/...`.
*   WebSocket connections to `/ws/...` are rewritten to `ws://144.126.215.218:8888/ws/...`.
This allows the PWA to communicate with the backend as if it were on the same domain.

---

## 7. Environment Variables (`.env.local`)
For local development, this file tells the PWA where to find the backend. **This file is not committed to version control.**

```env
# Connects directly to your DigitalOcean server for local testing
VITE_API_URL=http://144.126.215.218:8888
VITE_WS_URL=ws://144.126.215.218:8888
```

On Vercel, these are set in the project's environment variable settings to point to the proxied paths (e.g., `https://[your-app].vercel.app/api`). 