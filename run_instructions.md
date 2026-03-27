# NeuroVed AI - Premium Mental Health Web App

This project has been completely overhauled with a breathtaking modern UI (Glassmorphism & Animated Mesh Gradients) and fully functioning backend modules. 

## 1. Setup Environment
Ensure you have Python 3.9+ installed on your system.
Install the required packages:

```bash
pip install -r requirements.txt
```

## 2. Configuration (`.env`)
Create a `.env` file in the root directory (or use the one already present). You can use `.env.example` as a template.

```env
SECRET_KEY=your_secure_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```
**CRITICAL**: Without the `GEMINI_API_KEY`, the general chatbot and the OCR Analyzer features will not function correctly. The ML model inference will still work for mental health queries.

## 3. Database Initialization
The SQLite database will automatically initialize when you first run the app. It will create `instance/database.db` containing `user` and `storage_item` tables.

## 4. Run the Application
Start the Flask application:

```bash
python app.py
```

## 5. View the App
Open your web browser and navigate to:
**http://localhost:5000**

You will land on the modernized Landing page. From there, click "Get Started" to register a new account, or "Login" to access the Premium Dashboard.

## Included Modules
1. **Chatbot**: Real-time ML model classification displaying emotion percentages with a chart + Gemini fallback. Includes voice input and output.
2. **Storage Bot**: Two distinct secure vaults for Medical Reports and Medicines. Uploaded items are kept isolated per-user.
3. **Analyzer**: Image OCR using Gemini Vision 1.5 Flash. Predicts medicine names and keywords, offering instant Google Search links.
4. **Pincode Locator**: Enter a valid Indian 6-digit pin to locate the nearest mental health facilities.
