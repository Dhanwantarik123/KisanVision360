# KisanVision360+ — Responsive Advanced Build

## Included
- Flask + Blueprint architecture
- PostgreSQL / Supabase via `psycopg2`
- Responsive UI for mobile, tablet, laptop and desktop
- Mobile collapsible sidebar with overlay and ESC close
- RTL layout for Urdu, Kashmiri and Sindhi
- Google Translate centralized in `base.html`
- 20 supported languages
- Farmer, Consumer and Admin dashboards
- Weather, crop recommendation, smart irrigation, market/mandi, finance
- Government schemes, marketplace, wishlist, cart and orders
- Notifications, reports, tools, help and chatbot
- AI disease detection with 53 configured classes
- Disease image upload + prediction APIs
- Responsive master CSS and JavaScript

## Setup

1. Install Python 3.11.x.
2. Create a virtual environment:
   `python -m venv venv`
3. Activate it on Windows PowerShell:
   `.\venv\Scripts\Activate.ps1`
4. Install packages:
   `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and enter your own values.
6. Start:
   `python app.py`

## Disease model
The project expects:

`ai_models/disease_model.keras`

The configured disease class order is stored in:
- `ai_models/disease_classes.txt`
- `ai_models/disease_classes.json`

The server verifies that the loaded model output count matches the 53 configured classes.

## Responsive system
`static/css/responsive_master.css` is loaded after page CSS from `base.html`.

Breakpoints:
- 1200px and below: laptop adjustments
- 900px and below: tablet/mobile sidebar mode
- 600px and below: one-column forms/cards where required
- 420px and 360px: small-phone refinements

## Language
Google Translate is initialized once by `base.html`. The language page calls the global language function and saves the selected language through `/set-language`.

## Security
Do not commit `.env`, passwords, API keys or database credentials. Use `.env.example` as the template.
