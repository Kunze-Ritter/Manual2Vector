<x-filament-panels::page class="krai-chat-page">
    <style>
        .krai-chat-page {
            --krai-bg: #f3f4f6;
            --krai-panel: #ffffff;
            --krai-panel-dark: #0f172a;
            --krai-border: #e5e7eb;
            --krai-border-dark: #1f2937;
            --krai-text: #111827;
            --krai-muted: #6b7280;
            --krai-accent: #d97706;
            --krai-accent-soft: #fff7ed;
            --krai-user: #111827;
            --krai-assistant: #ffffff;
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.08), transparent 28%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
            padding: 0.5rem 0 1rem;
        }

        .dark .krai-chat-page {
            --krai-bg: #020617;
            --krai-text: #f9fafb;
            --krai-muted: #94a3b8;
            --krai-assistant: #111827;
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.08), transparent 26%),
                linear-gradient(180deg, #020617 0%, #0f172a 100%);
        }

        .krai-chat-page * {
            box-sizing: border-box;
        }

        .krai-chat-page {
            color: var(--krai-text);
        }

        .krai-chat-page button,
        .krai-chat-page textarea {
            font: inherit;
        }

        .krai-chat-layout {
            display: grid;
            grid-template-columns: 280px minmax(0, 1fr) 320px;
            grid-template-areas: "sidebar main inspector";
            gap: 1rem;
            min-height: calc(100vh - 10rem);
            align-items: start;
            color: var(--krai-text);
        }

        .krai-chat-panel {
            background: var(--krai-panel);
            border: 1px solid var(--krai-border);
            border-radius: 28px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            overflow: hidden;
        }

        .dark .krai-chat-panel {
            background: var(--krai-panel-dark);
            border-color: var(--krai-border-dark);
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28);
        }

        .krai-chat-sidebar,
        .krai-chat-inspector {
            display: flex;
            flex-direction: column;
        }

        .krai-chat-sidebar {
            grid-area: sidebar;
            min-width: 0;
        }

        .krai-chat-main {
            grid-area: main;
            display: grid;
            grid-template-rows: auto auto minmax(0, 1fr) auto;
            min-width: 0;
            min-height: calc(100vh - 10rem);
        }

        .krai-chat-inspector {
            grid-area: inspector;
            min-width: 0;
        }

        .krai-chat-sidebar-header {
            padding: 1.25rem;
            border-bottom: 1px solid var(--krai-border);
            background: linear-gradient(180deg, #fffdf7 0%, #ffffff 100%);
        }

        .krai-chat-brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .krai-chat-brand-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2.75rem;
            height: 2.75rem;
            border-radius: 1rem;
            background: #fef3c7;
            color: #b45309;
            flex: 0 0 auto;
        }

        .dark .krai-chat-brand-icon {
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
        }

        .krai-chat-eyebrow {
            margin: 0;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--krai-muted);
        }

        .krai-chat-title {
            margin: 0.2rem 0 0;
            font-size: 1.2rem;
            line-height: 1.2;
            font-weight: 700;
            color: var(--krai-text);
        }

        .krai-chat-subtitle {
            margin: 0.35rem 0 0;
            font-size: 0.92rem;
            line-height: 1.5;
            color: var(--krai-muted);
        }

        .krai-chat-primary-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.55rem;
            width: 100%;
            min-height: 2.9rem;
            margin-top: 1rem;
            padding: 0.8rem 1rem;
            border: 0;
            border-radius: 1rem;
            background: linear-gradient(135deg, #d97706, #f59e0b);
            color: #fff;
            font-size: 0.92rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 14px 28px rgba(217, 119, 6, 0.2);
        }

        .krai-chat-primary-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(217, 119, 6, 0.26);
        }

        .dark .krai-chat-sidebar-header {
            background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
            border-bottom-color: var(--krai-border-dark);
        }

        .krai-chat-sidebar-metrics,
        .krai-chat-main-metrics {
            display: grid;
            gap: 0.75rem;
        }

        .krai-chat-sidebar-metrics {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--krai-border);
        }

        .krai-chat-main-metrics {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e5e7eb;
            background: #f8fafc;
        }

        .dark .krai-chat-sidebar-metrics,
        .dark .krai-chat-main-metrics {
            border-bottom-color: var(--krai-border-dark);
            background: rgba(15, 23, 42, 0.72);
        }

        .krai-chat-metric {
            background: #f8fafc;
            border: 1px solid var(--krai-border);
            border-radius: 20px;
            padding: 0.85rem 1rem;
        }

        .krai-chat-metric-label {
            margin: 0;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--krai-muted);
        }

        .krai-chat-metric-value {
            margin: 0.35rem 0 0;
            font-size: 1.6rem;
            line-height: 1.1;
            font-weight: 700;
            color: var(--krai-text);
        }

        .krai-chat-metric-value.is-compact {
            font-size: 0.95rem;
            line-height: 1.4;
        }

        .dark .krai-chat-metric {
            background: #111827;
            border-color: var(--krai-border-dark);
        }

        .krai-chat-section-title {
            padding: 1rem 1.25rem 0;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--krai-muted);
        }

        .krai-chat-session-list,
        .krai-chat-command-list {
            padding: 1rem 0.75rem 1.25rem;
            overflow: auto;
        }

        .krai-chat-session-list {
            max-height: calc(100vh - 24rem);
        }

        .krai-chat-session-item,
        .krai-chat-command-item {
            background: #f8fafc;
            border: 1px solid transparent;
            border-radius: 20px;
            margin-bottom: 0.75rem;
            transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
        }

        .krai-chat-session-item:hover,
        .krai-chat-command-item:hover {
            transform: translateY(-1px);
        }

        .dark .krai-chat-session-item,
        .dark .krai-chat-command-item {
            background: #111827;
        }

        .krai-chat-session-item.is-active {
            border-color: #f59e0b;
            background: #fff7ed;
        }

        .krai-chat-session-trigger {
            width: 100%;
            padding: 1rem;
            border: 0;
            background: transparent;
            text-align: left;
            cursor: pointer;
        }

        .krai-chat-session-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
        }

        .krai-chat-session-copy {
            min-width: 0;
        }

        .krai-chat-session-title {
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.35;
            font-weight: 700;
            color: var(--krai-text);
        }

        .krai-chat-session-meta {
            margin: 0.35rem 0 0;
            font-size: 0.78rem;
            color: var(--krai-muted);
        }

        .krai-chat-badge-live {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.35rem 0.6rem;
            border-radius: 999px;
            background: #f59e0b;
            color: #fff;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }

        .dark .krai-chat-session-item.is-active {
            background: rgba(245, 158, 11, 0.12);
            border-color: rgba(245, 158, 11, 0.45);
        }

        .krai-chat-main-header {
            padding: 1.5rem;
            color: #fff;
            border-bottom: 1px solid #1f2937;
            background:
                radial-gradient(circle at top left, rgba(251, 191, 36, 0.28), transparent 34%),
                linear-gradient(135deg, #111827, #1f2937);
        }

        .krai-chat-main-header-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .krai-chat-main-identity {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .krai-chat-main-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 3rem;
            height: 3rem;
            border-radius: 1rem;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            backdrop-filter: blur(12px);
            flex: 0 0 auto;
        }

        .krai-chat-main-title {
            margin: 0.2rem 0 0;
            font-size: 1.35rem;
            line-height: 1.2;
            font-weight: 700;
            color: #fff;
        }

        .krai-chat-main-subtitle {
            margin: 0.35rem 0 0;
            font-size: 0.92rem;
            line-height: 1.5;
            color: rgba(255, 255, 255, 0.75);
        }

        .krai-chat-status-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            background: rgba(255, 255, 255, 0.08);
            color: #fff;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }

        .krai-chat-action-group {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
        }

        .krai-chat-main-body {
            overflow: auto;
            padding: 1.5rem;
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        }

        .krai-chat-message-stack {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .dark .krai-chat-main-body {
            background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
        }

        .krai-chat-empty {
            max-width: 46rem;
            margin: 0 auto;
            padding: 2.5rem 2rem;
            border-radius: 30px;
            border: 1px dashed #f59e0b;
            background: rgba(255, 255, 255, 0.9);
            text-align: center;
        }

        .dark .krai-chat-empty {
            background: rgba(17, 24, 39, 0.9);
            border-color: rgba(245, 158, 11, 0.45);
        }

        .krai-chat-message-row {
            display: flex;
            margin-bottom: 1rem;
        }

        .krai-chat-message-row.is-user {
            justify-content: flex-end;
        }

        .krai-chat-message-row.is-assistant {
            justify-content: flex-start;
        }

        .krai-chat-bubble {
            max-width: 85%;
            border-radius: 28px;
            padding: 1rem 1.25rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
            line-height: 1.6;
        }

        .krai-chat-bubble-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .krai-chat-bubble-role {
            margin: 0;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.22em;
            text-transform: uppercase;
        }

        .krai-chat-bubble-time {
            margin: 0;
            font-size: 0.72rem;
            color: inherit;
            opacity: 0.68;
        }

        .krai-chat-message-text {
            margin: 0.7rem 0 0;
            white-space: pre-wrap;
            font-size: 0.96rem;
            line-height: 1.7;
        }

        .krai-chat-agent-mark {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }

        .krai-chat-agent-mark-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 0.8rem;
            background: #fef3c7;
            color: #b45309;
            flex: 0 0 auto;
        }

        .dark .krai-chat-agent-mark-icon {
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
        }

        .krai-chat-bubble-user {
            background: var(--krai-user);
            color: #fff;
            border-bottom-right-radius: 10px;
        }

        .krai-chat-bubble-assistant {
            background: var(--krai-assistant);
            color: var(--krai-text);
            border: 1px solid var(--krai-border);
            border-bottom-left-radius: 10px;
        }

        .dark .krai-chat-bubble-assistant {
            background: #111827;
            color: #f9fafb;
            border-color: var(--krai-border-dark);
        }

        .krai-chat-composer {
            padding: 1.25rem 1.5rem 1.5rem;
            border-top: 1px solid var(--krai-border);
            background: #fff;
        }

        .dark .krai-chat-composer {
            background: #0f172a;
            border-top-color: var(--krai-border-dark);
        }

        .krai-chat-composer-shell {
            border: 1px solid var(--krai-border);
            border-radius: 30px;
            background: #f8fafc;
            padding: 0.85rem;
        }

        .krai-chat-composer-help {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .krai-chat-composer-textarea {
            width: 100%;
            min-height: 5rem;
            resize: vertical;
            border: 0;
            background: transparent;
            padding: 0.85rem 0.95rem;
            color: var(--krai-text);
            font-size: 0.98rem;
            line-height: 1.65;
            outline: none;
        }

        .krai-chat-composer-textarea::placeholder {
            color: #9ca3af;
        }

        .dark .krai-chat-composer-textarea::placeholder {
            color: #64748b;
        }

        .dark .krai-chat-composer-shell {
            background: #111827;
            border-color: var(--krai-border-dark);
        }

        .krai-chat-inspector-header {
            padding: 1.25rem;
            border-bottom: 1px solid var(--krai-border);
            background: #f8fafc;
        }

        .dark .krai-chat-inspector-header {
            background: rgba(17, 24, 39, 0.78);
            border-bottom-color: var(--krai-border-dark);
        }

        .krai-chat-inspector-body {
            padding: 1.25rem;
            overflow: auto;
        }

        .krai-chat-status-card {
            padding: 1rem;
            border-radius: 22px;
            border: 1px solid var(--krai-border);
            background: #f8fafc;
            margin-bottom: 1.25rem;
        }

        .krai-chat-definition-list {
            margin: 1rem 0 0;
            padding: 0;
        }

        .krai-chat-definition-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.7rem 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        }

        .krai-chat-definition-row:last-child {
            border-bottom: 0;
            padding-bottom: 0;
        }

        .dark .krai-chat-definition-row {
            border-bottom-color: rgba(51, 65, 85, 0.6);
        }

        .krai-chat-definition-term {
            margin: 0;
            font-size: 0.85rem;
            color: var(--krai-muted);
        }

        .krai-chat-definition-value {
            margin: 0;
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--krai-text);
            text-align: right;
        }

        .krai-chat-section-heading {
            margin: 0;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--krai-muted);
        }

        .dark .krai-chat-status-card {
            background: #111827;
            border-color: var(--krai-border-dark);
        }

        .krai-chat-page h2,
        .krai-chat-page h3,
        .krai-chat-page p,
        .krai-chat-page dt,
        .krai-chat-page dd,
        .krai-chat-page span,
        .krai-chat-page button,
        .krai-chat-page code,
        .krai-chat-page textarea {
            font-family: Inter Variable, Inter, ui-sans-serif, system-ui, sans-serif;
        }

        .krai-chat-page p,
        .krai-chat-page dt,
        .krai-chat-page dd,
        .krai-chat-page span {
            color: inherit;
        }

        .krai-chat-page textarea {
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .krai-chat-page code {
            display: inline-block;
            padding: 0.1rem 0.35rem;
            border-radius: 8px;
            background: rgba(148, 163, 184, 0.14);
            color: #92400e;
            font-size: 0.8rem;
        }

        .dark .krai-chat-page code {
            color: #fbbf24;
            background: rgba(245, 158, 11, 0.12);
        }

        .krai-chat-action-btn,
        .krai-chat-pill,
        .krai-chat-send-btn {
            appearance: none;
            border: 0;
            cursor: pointer;
            transition: all 120ms ease;
        }

        .krai-chat-action-btn {
            padding: 0.75rem 1rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.08);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.14);
        }

        .krai-chat-action-btn:hover {
            background: rgba(255, 255, 255, 0.14);
        }

        .krai-chat-pill {
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            border: 1px solid #d1d5db;
            background: #fff;
            color: #374151;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .krai-chat-pill:hover {
            border-color: #f59e0b;
            color: #b45309;
            background: #fffaf0;
        }

        .dark .krai-chat-pill {
            background: #111827;
            border-color: #374151;
            color: #e5e7eb;
        }

        .dark .krai-chat-pill:hover {
            border-color: #f59e0b;
            color: #fbbf24;
            background: rgba(245, 158, 11, 0.08);
        }

        .krai-chat-send-btn {
            min-width: 122px;
            height: 3rem;
            border-radius: 16px;
            background: #111827;
            color: #fff;
            padding: 0 1.1rem;
            font-weight: 700;
        }

        .krai-chat-send-btn:hover {
            background: #000;
        }

        .dark .krai-chat-send-btn {
            background: #f59e0b;
            color: #111827;
        }

        .dark .krai-chat-send-btn:hover {
            background: #fbbf24;
        }

        .krai-chat-delete-btn {
            background: transparent;
            border: 0;
            cursor: pointer;
            padding: 0.25rem 0;
            color: #dc2626;
            font-size: 0.76rem;
            font-weight: 700;
        }

        .krai-chat-label {
            color: var(--krai-muted);
            font-size: 0.75rem;
        }

        .krai-chat-prose {
            margin-top: 0.75rem;
            color: inherit;
        }

        .krai-chat-prose p,
        .krai-chat-prose li,
        .krai-chat-prose ul,
        .krai-chat-prose ol,
        .krai-chat-prose pre {
            color: inherit;
        }

        .krai-chat-prose p:first-child {
            margin-top: 0;
        }

        .krai-chat-prose p:last-child {
            margin-bottom: 0;
        }

        .krai-chat-prose pre {
            border-radius: 16px;
            background: #0f172a;
            color: #f8fafc;
            padding: 1rem;
            overflow: auto;
        }

        .krai-chat-prose ul,
        .krai-chat-prose ol {
            padding-left: 1.25rem;
        }

        @media (max-width: 1535px) {
            .krai-chat-layout {
                grid-template-columns: 280px minmax(0, 1fr);
                grid-template-areas:
                    "sidebar main"
                    "inspector main";
            }

            .krai-chat-main-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .krai-chat-inspector {
                align-self: start;
            }
        }

        @media (max-width: 1024px) {
            .krai-chat-layout {
                grid-template-columns: 1fr;
                grid-template-areas:
                    "main"
                    "sidebar"
                    "inspector";
            }

            .krai-chat-main {
                min-height: 70vh;
            }

            .krai-chat-session-list {
                max-height: 22rem;
            }
        }

        @media (max-width: 767px) {
            .krai-chat-sidebar-metrics,
            .krai-chat-main-metrics {
                grid-template-columns: 1fr;
            }

            .krai-chat-main-header-inner {
                flex-direction: column;
                align-items: flex-start;
            }

            .krai-chat-composer-help {
                align-items: flex-start;
            }

            .krai-chat-bubble {
                max-width: 100%;
            }
        }
    </style>
    @php
        $sessions = $sessions ?? $chatSessions ?? [];
        $messages = $messages ?? [];
        $commandCatalog = $commandCatalog ?? [];
        $workspaceSnapshot = $workspaceSnapshot ?? [];
        $healthOk = $healthOk ?? false;
        $agentHealth = $agentHealth ?? [];
        $agentStatus = $agentStatus ?? ($agentHealth['status'] ?? 'unknown');
        $agentVersion = $agentVersion ?? ($agentHealth['version'] ?? 'n/a');
    @endphp

    @if ($healthOk)
        <div class="krai-chat-layout">
            <aside class="krai-chat-panel krai-chat-sidebar overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-950">
                <div class="krai-chat-sidebar-header border-b border-gray-200 bg-gradient-to-br from-gray-50 to-white px-5 py-5 dark:border-gray-800 dark:from-gray-900 dark:to-gray-950">
                    <div class="krai-chat-brand">
                        <div class="krai-chat-brand-icon">
                            <x-filament::icon icon="heroicon-o-command-line" class="h-5 w-5" />
                        </div>
                        <div>
                            <p class="krai-chat-eyebrow">Agent Console</p>
                            <p class="krai-chat-title">KRAI Command Hub</p>
                            <p class="krai-chat-subtitle">Sessions, Verlauf und Schnellzugriffe</p>
                        </div>
                    </div>

                    <button wire:click="newChat" type="button" class="krai-chat-primary-btn">
                        <x-filament::icon icon="heroicon-o-plus" class="h-4 w-4" />
                        <span>Neuer Workspace</span>
                    </button>
                </div>

                <div class="krai-chat-sidebar-metrics border-b border-gray-200 px-5 py-4 dark:border-gray-800">
                        <div class="krai-chat-metric">
                            <p class="krai-chat-metric-label">Sessions</p>
                            <p class="krai-chat-metric-value">{{ $workspaceSnapshot['sessions'] ?? 0 }}</p>
                        </div>
                        <div class="krai-chat-metric">
                            <p class="krai-chat-metric-label">Messages</p>
                            <p class="krai-chat-metric-value">{{ $workspaceSnapshot['messages'] ?? 0 }}</p>
                        </div>
                </div>

                <div class="krai-chat-section-title px-5 pt-4">
                    <p class="text-[11px] uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400">Conversation Threads</p>
                </div>

                <div class="krai-chat-session-list max-h-[34rem] space-y-2 overflow-y-auto px-3 py-4">
                    @forelse ($sessions as $chatSession)
                        @php
                            $isActive = ($chatSession['session_key'] ?? '') === ($sessionId ?? '');
                            $title = $chatSession['title'] ?: 'Unbenannter Chat';
                        @endphp
                        <div class="krai-chat-session-item {{ $isActive ? 'is-active' : '' }}">
                            <button
                                wire:click="switchSession('{{ $chatSession['session_key'] }}')"
                                class="krai-chat-session-trigger"
                            >
                                <div class="krai-chat-session-row">
                                    <div class="krai-chat-session-copy">
                                        <p class="krai-chat-session-title">{{ $title }}</p>
                                        <p class="krai-chat-session-meta">
                                            {{ \Carbon\Carbon::parse($chatSession['last_active'] ?? now())->format('d.m.Y H:i') }}
                                        </p>
                                    </div>
                                    @if ($isActive)
                                        <span class="krai-chat-badge-live">
                                            Live
                                        </span>
                                    @endif
                                </div>
                            </button>
                            <div class="px-4 pb-3">
                                <button
                                    wire:click.stop="deleteSession('{{ $chatSession['session_key'] }}')"
                                    class="krai-chat-delete-btn text-xs font-medium text-red-600 transition hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                                >
                                    Session loeschen
                                </button>
                            </div>
                        </div>
                    @empty
                        <div class="rounded-2xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
                            Noch keine Sessions vorhanden.
                        </div>
                    @endforelse
                </div>

                <div class="border-t border-gray-200 px-5 py-4 dark:border-gray-800">
                    <p class="text-[11px] uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400">Quick Start</p>
                    <div class="mt-3 flex flex-wrap gap-2">
                        <button wire:click="$set('currentMessage', '/help')" class="krai-chat-pill rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">/help</button>
                        <button wire:click="$set('currentMessage', '/diagnose 13.B9')" class="krai-chat-pill rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">/diagnose</button>
                        <button wire:click="$set('currentMessage', '/lookup Ricoh 5')" class="krai-chat-pill rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">/lookup</button>
                    </div>
                </div>
            </aside>

            <section class="krai-chat-panel krai-chat-main overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-950">
                <div class="krai-chat-main-header border-b border-gray-200 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.28),_transparent_34%),linear-gradient(135deg,#111827,#1f2937)] px-6 py-5 text-white dark:border-gray-800">
                    <div class="krai-chat-main-header-inner flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <div class="krai-chat-main-identity">
                            <div class="krai-chat-main-icon">
                                <x-filament::icon icon="heroicon-o-sparkles" class="h-6 w-6" />
                            </div>
                            <div>
                                <p class="krai-chat-eyebrow" style="color: rgba(255,255,255,0.62);">Live Agent Workspace</p>
                                <div class="flex flex-wrap items-center gap-2">
                                    <h2 class="krai-chat-main-title">KRAI AI Workspace</h2>
                                    <span class="krai-chat-status-pill">
                                        {{ $agentStatus }}
                                    </span>
                                </div>
                                <p class="krai-chat-main-subtitle">{{ $sessionTitle ?: 'Aktive Session' }} · Agent {{ $agentVersion }}</p>
                            </div>
                        </div>

                        <div class="krai-chat-action-group">
                            <button wire:click="clearHistory" class="krai-chat-action-btn">
                                Verlauf loeschen
                            </button>
                            <button wire:click="$refresh" class="krai-chat-action-btn">
                                Refresh
                            </button>
                        </div>
                    </div>
                </div>

                <div class="grid h-full grid-rows-[auto_minmax(0,1fr)_auto]">
                    <div class="krai-chat-main-metrics border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-800 dark:bg-gray-900/80">
                            <div class="krai-chat-metric">
                                <p class="krai-chat-metric-label">Products</p>
                                <p class="krai-chat-metric-value">{{ $workspaceSnapshot['products'] ?? 0 }}</p>
                            </div>
                            <div class="krai-chat-metric">
                                <p class="krai-chat-metric-label">Errors</p>
                                <p class="krai-chat-metric-value">{{ $workspaceSnapshot['errors'] ?? 0 }}</p>
                            </div>
                            <div class="krai-chat-metric">
                                <p class="krai-chat-metric-label">Documents</p>
                                <p class="krai-chat-metric-value">{{ $workspaceSnapshot['documents'] ?? 0 }}</p>
                            </div>
                            <div class="krai-chat-metric">
                                <p class="krai-chat-metric-label">Mode</p>
                                <p class="krai-chat-metric-value is-compact">Agent + Tools</p>
                            </div>
                    </div>

                    <div class="krai-chat-main-body min-h-0 overflow-y-auto bg-gradient-to-b from-gray-50 to-white px-6 py-6 dark:from-gray-900 dark:to-gray-950">
                        <div class="krai-chat-message-stack">
                            @if (count($messages) === 0)
                                <div class="krai-chat-empty mx-auto max-w-2xl rounded-[2rem] border border-dashed border-amber-300 bg-white/80 px-8 py-10 text-center shadow-sm dark:border-amber-500/40 dark:bg-gray-900/80">
                                    <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-[1.75rem] bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                                        <x-filament::icon icon="heroicon-o-sparkles" class="h-10 w-10" />
                                    </div>
                                    <h3 class="mt-5 text-2xl font-semibold text-gray-900 dark:text-white">OpenWebUI-artiger Agent Workspace</h3>
                                    <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                                        Freie LLM-Chats kombiniert mit Slash-Commands fuer strukturierte DB-Abfragen und Diagnose-Workflows.
                                    </p>

                                    <div class="mt-6 flex flex-wrap justify-center gap-2">
                                        <button wire:click="$set('currentMessage', '/help')" class="krai-chat-pill rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-gray-900">/help</button>
                                        <button wire:click="$set('currentMessage', '/diagnose 13.B9')" class="krai-chat-pill rounded-full border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">/diagnose 13.B9</button>
                                        <button wire:click="$set('currentMessage', '/lookup Ricoh 5')" class="krai-chat-pill rounded-full border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">/lookup Ricoh 5</button>
                                        <button wire:click="$set('currentMessage', 'Fasse die wichtigsten Firecrawl-Fehler aus dem Dashboard zusammen.')" class="krai-chat-pill rounded-full border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300">Freier Prompt</button>
                                    </div>
                                </div>
                            @endif

                            @foreach ($messages as $message)
                                @if (($message['role'] ?? '') === 'user')
                                    <div class="krai-chat-message-row is-user flex justify-end">
                                        <div class="krai-chat-bubble krai-chat-bubble-user">
                                            <div class="krai-chat-bubble-head">
                                                <p class="krai-chat-bubble-role">Operator</p>
                                                <p class="krai-chat-bubble-time">{{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}</p>
                                            </div>
                                            <p class="krai-chat-message-text">{{ $message['content'] ?? '' }}</p>
                                        </div>
                                    </div>
                                @else
                                    <div class="krai-chat-message-row is-assistant flex justify-start">
                                        <div class="krai-chat-bubble krai-chat-bubble-assistant">
                                            <div class="krai-chat-bubble-head">
                                                <div class="krai-chat-agent-mark">
                                                    <div class="krai-chat-agent-mark-icon">
                                                        <x-filament::icon icon="heroicon-o-sparkles" class="h-4 w-4" />
                                                    </div>
                                                    <p class="krai-chat-bubble-role" style="color: var(--krai-muted);">KRAI Agent</p>
                                                </div>
                                                <p class="krai-chat-bubble-time" style="color: var(--krai-muted);">{{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}</p>
                                            </div>
                                            <div class="krai-chat-prose prose prose-sm mt-3 max-w-none dark:prose-invert">
                                                {!! \Illuminate\Support\Str::markdown($message['content'] ?? '', ['html_input' => 'strip', 'allow_unsafe_links' => false]) !!}
                                            </div>
                                        </div>
                                    </div>
                                @endif
                            @endforeach

                            <div wire:loading.flex wire:target="sendMessage" class="justify-start">
                                <div class="max-w-[18rem] rounded-[2rem] rounded-bl-md border border-gray-200 bg-white px-5 py-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
                                    <div class="flex items-center gap-3">
                                        <div class="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                                            <x-filament::icon icon="heroicon-o-sparkles" class="h-4 w-4" />
                                        </div>
                                        <span class="text-[10px] font-semibold uppercase tracking-[0.25em] text-gray-500 dark:text-gray-400">Thinking</span>
                                    </div>
                                    <div class="mt-3 flex gap-1.5">
                                        <span class="h-2.5 w-2.5 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.2s]"></span>
                                        <span class="h-2.5 w-2.5 animate-bounce rounded-full bg-amber-400 [animation-delay:-0.1s]"></span>
                                        <span class="h-2.5 w-2.5 animate-bounce rounded-full bg-amber-400"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="krai-chat-composer border-t border-gray-200 bg-white px-6 py-5 dark:border-gray-800 dark:bg-gray-950">
                        <div class="mb-3 flex flex-wrap gap-2">
                            @foreach (collect($commandCatalog)->take(6) as $command)
                                <button
                                    wire:click="$set('currentMessage', '{{ $command['example'] }}')"
                                    class="krai-chat-pill rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-amber-500 hover:text-amber-600 dark:border-gray-700 dark:text-gray-300 dark:hover:border-amber-400 dark:hover:text-amber-300"
                                >
                                    {{ $command['command'] }}
                                </button>
                            @endforeach
                        </div>

                        <form wire:submit.prevent="sendMessage" class="krai-chat-composer-shell">
                            <div class="flex flex-col gap-3 lg:flex-row lg:items-end">
                                <div class="min-w-0 flex-1">
                                    <textarea
                                        wire:model="currentMessage"
                                        rows="3"
                                        placeholder="Nachricht oder /command eingeben..."
                                        class="krai-chat-composer-textarea"
                                        x-on:keydown.enter.prevent="$wire.sendMessage()"
                                    ></textarea>
                                </div>
                                <div class="krai-chat-composer-help">
                                    <p class="krai-chat-label">
                                        Freie Frage oder Tool-Command wie <code>/diagnose 13.B9</code>
                                    </p>
                                    <button
                                        type="submit"
                                        class="krai-chat-send-btn inline-flex h-12 items-center justify-center rounded-2xl bg-gray-900 px-5 text-sm font-semibold text-white transition hover:bg-black disabled:bg-gray-300 dark:bg-amber-500 dark:text-gray-950 dark:hover:bg-amber-400"
                                        wire:loading.attr="disabled"
                                        wire:target="sendMessage"
                                    >
                                        <span wire:loading.remove wire:target="sendMessage">Senden</span>
                                        <span wire:loading wire:target="sendMessage">Laeuft...</span>
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </section>

            <aside class="krai-chat-panel krai-chat-inspector overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-950">
                <div class="krai-chat-inspector-header border-b border-gray-200 bg-gray-50 px-5 py-5 dark:border-gray-800 dark:bg-gray-900/70">
                    <p class="krai-chat-eyebrow">Operations</p>
                    <p class="krai-chat-title">Tool Inspector</p>
                    <p class="krai-chat-subtitle">Befehle, Datenabdeckung und Agent-Status im Blick.</p>
                </div>

                <div class="krai-chat-inspector-body space-y-5 px-5 py-5">
                    <div class="krai-chat-status-card">
                        <div class="flex items-center justify-between gap-3">
                            <p class="krai-chat-section-heading">Agent Status</p>
                            <span class="rounded-full {{ $healthOk ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : 'bg-red-500/15 text-red-700 dark:text-red-300' }} px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide">
                                {{ $healthOk ? 'online' : 'offline' }}
                            </span>
                        </div>
                        <dl class="krai-chat-definition-list">
                            <div class="krai-chat-definition-row">
                                <dt class="krai-chat-definition-term">Status</dt>
                                <dd class="krai-chat-definition-value">{{ $agentStatus }}</dd>
                            </div>
                            <div class="krai-chat-definition-row">
                                <dt class="krai-chat-definition-term">Version</dt>
                                <dd class="krai-chat-definition-value">{{ $agentVersion }}</dd>
                            </div>
                            <div class="krai-chat-definition-row">
                                <dt class="krai-chat-definition-term">Last Check</dt>
                                <dd class="krai-chat-definition-value">{{ now()->format('H:i') }}</dd>
                            </div>
                        </dl>
                    </div>

                    <div>
                        <p class="krai-chat-section-heading">Command Catalog</p>
                        <div class="krai-chat-command-list mt-3 space-y-3">
                            @foreach ($commandCatalog as $command)
                                <button
                                    wire:click="$set('currentMessage', '{{ $command['example'] }}')"
                                    class="krai-chat-command-item w-full rounded-2xl border border-gray-200 bg-white p-4 text-left transition hover:border-amber-400 hover:bg-amber-50/60 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-amber-500/40 dark:hover:bg-amber-500/10"
                                >
                                    <div class="flex items-center justify-between gap-3">
                                        <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ $command['command'] }}</span>
                                        <span class="text-[10px] uppercase tracking-[0.2em] text-gray-400">{{ $command['label'] }}</span>
                                    </div>
                                    <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">{{ $command['description'] }}</p>
                                    <code class="mt-3 block text-xs text-amber-700 dark:text-amber-300">{{ $command['example'] }}</code>
                                </button>
                            @endforeach
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    @else
        <div class="flex min-h-[420px] items-center justify-center">
            <x-filament::card class="max-w-lg">
                <div class="p-8 text-center">
                    <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-[1.75rem] bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300">
                        <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-10 w-10" />
                    </div>
                    <h3 class="mt-5 text-xl font-semibold text-gray-900 dark:text-white">AI Agent ist offline</h3>
                    <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        Der Workspace ist verfuegbar, aber der Agent antwortet aktuell nicht. Sobald die Verbindung steht, kannst du freie Prompts und Slash-Commands nutzen.
                    </p>
                    <div class="mt-6">
                        <x-filament::button wire:click="retryConnection" icon="heroicon-o-arrow-path" color="danger">
                            Verbindung erneut pruefen
                        </x-filament::button>
                    </div>
                </div>
            </x-filament::card>
        </div>
    @endif
</x-filament-panels::page>
