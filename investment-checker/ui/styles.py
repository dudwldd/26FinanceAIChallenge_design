"""Global visual system for the Portfolio Thesis Checker."""

import streamlit as st


def apply_global_styles() -> None:
    """Apply the Figma-inspired visual tokens to Streamlit widgets."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&family=Noto+Serif+KR:wght@500;600&family=Playfair+Display:wght@600&display=swap');

        :root {
            --court-ink: #202124;
            --court-muted: #72767f;
            --court-line: #e7e8eb;
            --court-soft: #f7f8fa;
            --court-coral: #ef5447;
            --court-coral-hover: #dc463b;
            --court-mint: #20b989;
            --court-warning: #e8a600;
            --court-radius: 12px;
        }

        .stApp {
            background: #ffffff;
            color: var(--court-ink);
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
            border-bottom: 1px solid var(--court-line);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1280px;
            padding-top: 2.75rem;
            padding-left: 2.75rem;
            padding-right: 2.75rem;
            padding-bottom: 6rem;
        }

        h1, h2, h3 {
            color: var(--court-ink);
            letter-spacing: -0.035em;
        }

        h1 {
            font-family: "Playfair Display", Georgia, "Times New Roman", serif;
            font-size: clamp(2.25rem, 5vw, 3.45rem) !important;
            line-height: 1.08 !important;
            font-weight: 500 !important;
            margin-bottom: 0.55rem !important;
        }

        h2 {
            font-size: 1.35rem !important;
            font-weight: 650 !important;
            margin-top: 2rem !important;
        }

        p, label, [data-testid="stCaptionContainer"] {
            line-height: 1.65;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--court-muted);
        }

        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stDataFrame"],
        div[data-testid="stMetric"] {
            border: 1px solid var(--court-line);
            border-radius: var(--court-radius);
            background: #ffffff;
            box-shadow: 0 8px 30px rgba(25, 31, 42, 0.035);
        }

        [data-testid="stForm"] {
            padding: 1.35rem 1.4rem 1.5rem;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div {
            border-color: var(--court-line) !important;
            border-radius: 9px !important;
            background: var(--court-soft) !important;
        }

        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="textarea"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--court-coral) !important;
            box-shadow: 0 0 0 1px var(--court-coral) !important;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            min-height: 2.85rem;
            border-radius: 9px;
            border: 1px solid var(--court-line);
            font-weight: 650;
            transition: border-color 150ms ease, color 150ms ease,
                background 150ms ease, transform 150ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            color: var(--court-coral);
            border-color: var(--court-coral);
            transform: translateY(-1px);
        }

        .stFormSubmitButton > button {
            color: #ffffff;
            background: var(--court-coral);
            border-color: var(--court-coral);
        }

        .stFormSubmitButton > button:hover {
            color: #ffffff;
            background: var(--court-coral-hover);
            border-color: var(--court-coral-hover);
        }

        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed #cfd2d8;
            border-radius: var(--court-radius);
            background: var(--court-soft);
        }

        div[data-testid="stMetric"] {
            padding: 1rem 1.1rem;
        }

        [data-testid="stAlert"] {
            border-radius: var(--court-radius);
        }

        hr {
            border-color: var(--court-line) !important;
        }

        .login-shell {
            margin-top: 1.5rem;
        }

        .login-intro {
            min-height: 540px;
            padding: 5.5rem 4.5rem 4rem 0.5rem;
            border-right: 1px solid var(--court-line);
        }

        .login-eyebrow {
            display: inline-block;
            margin-bottom: 1.2rem;
            padding: 0.38rem 0.65rem;
            border-radius: 999px;
            background: #fff1ef;
            color: var(--court-coral);
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }

        .login-intro h1 {
            margin: 0 0 1.2rem !important;
            max-width: 590px;
            font-size: clamp(2rem, 3.1vw, 2.75rem) !important;
            line-height: 1.18 !important;
        }

        .login-lead {
            color: var(--court-muted);
            font-size: 0.98rem;
        }

        .login-feature-list {
            display: grid;
            gap: 0.85rem;
            margin-top: 2.3rem;
            color: #535761;
            font-size: 0.9rem;
        }

        .login-feature-list span {
            display: inline-grid;
            width: 1.6rem;
            height: 1.6rem;
            margin-right: 0.45rem;
            place-items: center;
            border-radius: 7px;
            background: #fff1ef;
            color: var(--court-coral);
            font-weight: 800;
        }

        .login-form-heading {
            padding-top: 4.7rem;
        }

        .login-form-heading h2 {
            margin: 0 0 0.15rem !important;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.9rem !important;
            font-weight: 500 !important;
        }

        .login-form-heading + [data-testid="stForm"] {
            margin-top: 1.3rem;
            padding: 0;
            border: 0;
            box-shadow: none;
        }

        .login-help {
            padding-top: 0.55rem;
            color: var(--court-coral);
            font-size: 0.82rem;
            text-align: right;
        }

        .login-divider {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 1.25rem 0;
            color: #a0a3a9;
            font-size: 0.76rem;
        }

        .login-divider::before,
        .login-divider::after {
            content: "";
            height: 1px;
            flex: 1;
            background: var(--court-line);
        }

        .login-signup {
            margin-top: 1.1rem;
            color: var(--court-muted);
            font-size: 0.8rem;
            text-align: center;
        }

        .login-signup span {
            color: var(--court-coral);
            font-weight: 700;
        }

        .workflow-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: -1.25rem 0 3.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--court-line);
            font-family: Georgia, "Times New Roman", serif;
        }

        .workflow-steps {
            display: flex;
            gap: 1.5rem;
            color: #a0a4ac;
            font-family: sans-serif;
            font-size: 0.78rem;
        }

        .workflow-step span {
            display: inline-block;
            width: 6px;
            height: 6px;
            margin-right: 0.4rem;
            border-radius: 50%;
            background: #d8dbe0;
            vertical-align: middle;
        }

        .workflow-step.is-active {
            color: var(--court-ink);
            font-weight: 700;
        }

        .workflow-step.is-active span {
            background: var(--court-coral);
        }

        .workflow-step.is-complete span {
            background: var(--court-mint);
        }

        .analysis-loading {
            max-width: 620px;
            margin: 3.5rem auto 0;
            text-align: center;
        }

        .analysis-loading h1 {
            margin-top: 1.25rem !important;
            font-size: 2.35rem !important;
        }

        .loading-spinner {
            width: 74px;
            height: 74px;
            margin: auto;
            border: 5px solid #eef0ff;
            border-top-color: #646cff;
            border-radius: 50%;
            animation: court-spin 0.9s linear infinite;
        }

        @keyframes court-spin {
            to { transform: rotate(360deg); }
        }

        .loading-lead {
            color: #76849f;
        }

        .loading-card {
            margin-top: 2.6rem;
            padding: 1.4rem 1.7rem;
            border: 1px solid #dde2ed;
            border-radius: 18px;
            background: #ffffff;
            text-align: left;
            box-shadow: 0 10px 35px rgba(42, 55, 82, 0.04);
        }

        .loading-stage {
            position: relative;
            display: grid;
            grid-template-columns: 38px 1fr;
            min-height: 76px;
            color: #a3adbf;
        }

        .loading-stage:not(:last-child)::after {
            content: "";
            position: absolute;
            top: 34px;
            bottom: -2px;
            left: 15px;
            width: 2px;
            background: #e5e9f1;
        }

        .loading-stage.complete:not(:last-child)::after,
        .loading-stage.active:not(:last-child)::after {
            background: #666cff;
        }

        .loading-node {
            z-index: 1;
            display: grid;
            width: 32px;
            height: 32px;
            place-items: center;
            border: 2px solid #e1e6ef;
            border-radius: 50%;
            background: #f8f9fc;
            font-weight: 800;
        }

        .loading-stage strong {
            display: block;
            padding-top: 0.25rem;
            font-size: 0.98rem;
        }

        .loading-stage p {
            margin: 0.15rem 0 0;
            font-size: 0.86rem;
        }

        .loading-stage.active,
        .loading-stage.complete {
            color: #6068ff;
        }

        .loading-stage.active .loading-node {
            animation: court-spin 1.1s linear infinite;
        }

        .loading-stage.complete .loading-node {
            color: #ffffff;
            border-color: #646cff;
            background: #646cff;
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .portfolio-card-title
        ) {
            margin-bottom: 1.4rem;
            padding: 3rem 3.2rem 3.1rem !important;
            border: 1px solid #dbe3ee !important;
            border-radius: 22px !important;
            background: #ffffff !important;
            box-shadow: 0 3px 12px rgba(43, 59, 82, 0.035) !important;
        }

        .portfolio-card-title {
            margin: 0 0 2.25rem !important;
            padding: 0 !important;
            font-family: "Noto Serif KR", "Batang", serif !important;
            font-size: 1.55rem !important;
            font-weight: 500 !important;
            letter-spacing: -0.04em;
            line-height: 1.45 !important;
        }

        .portfolio-card-title.thesis {
            margin-bottom: 0.45rem !important;
        }

        .portfolio-card-copy {
            margin: 0 0 1.25rem;
            color: #8ea0b9;
            font-size: 0.95rem;
        }

        .portfolio-column-label {
            padding: 0 0.3rem 0.85rem;
            border-bottom: 1px solid #dce4ef;
            color: #93a3ba;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
        }

        .portfolio-column-label.right {
            text-align: right;
        }

        .portfolio-total {
            padding-top: 0.65rem;
            color: #94a3b8;
            text-align: right;
        }

        .portfolio-total strong {
            margin-left: 0.35rem;
            font-size: 1.18rem;
            font-style: italic;
        }

        .portfolio-total.valid strong {
            color: #10b981;
        }

        .portfolio-total.invalid strong {
            color: var(--court-coral);
        }

        .portfolio-rule {
            height: 1px;
            margin: 1rem 0 0.95rem;
            background: #dce4ef;
        }

        button[kind="primary"] {
            color: #ffffff !important;
            border-color: var(--court-coral) !important;
            background: var(--court-coral) !important;
        }

        button[kind="primary"]:hover {
            border-color: var(--court-coral-hover) !important;
            background: var(--court-coral-hover) !important;
        }

        div[data-testid="stNumberInput"] input {
            font-weight: 700;
            text-align: right;
        }

        div[data-testid="stNumberInput"] button {
            display: none;
        }

        div[data-baseweb="input"] > div {
            min-height: 52px;
        }

        div[data-testid="stTextInput"] input {
            color: #111827;
            font-weight: 600;
            letter-spacing: 0.04em;
        }

        @media (max-width: 720px) {
            [data-testid="stMainBlockContainer"] {
                padding: 2rem 1rem 4rem;
            }

            [data-testid="stForm"] {
                padding: 1rem;
            }

            div[data-testid="stVerticalBlock"]:has(
                > div[data-testid="stElementContainer"] .portfolio-card-title
            ) {
                padding: 1.6rem 1.3rem 1.8rem !important;
                border-radius: 17px;
            }

            .login-intro {
                min-height: auto;
                padding: 2rem 0 1.5rem;
                border-right: 0;
                border-bottom: 1px solid var(--court-line);
            }

            .login-form-heading {
                padding-top: 1rem;
            }

            .workflow-nav,
            .workflow-steps {
                align-items: flex-start;
            }

            .workflow-nav {
                gap: 1rem;
            }

            .workflow-steps {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.45rem 0.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
