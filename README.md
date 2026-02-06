# Mrs. Higgins: The Social-Engineering Honeypot Agent

**Submission for India AI Impact Buildathon**
*(Note: Hosted on Render Free Tier. Please allow 30-60 seconds for the server to "wake up" upon first load.)*

---

## Project Overview
Mrs. Higgins is a "Cyber-Honeypot" designed to engage scammers through **Weaponized Incompetence**. While typical tools simply block, Mrs. Higgins social-engineers the attacker to extract traceable intelligence (UPI IDs, Phone Numbers, and Bank Accounts) while maintaining the persona of a tech-confused 72-year-old grandmother.

## Dual-Layer Intelligence System

### 1. The Gatekeeper (The Shield)
The Gatekeeper is a high-precision classifier that uses **Collective Signal Analysis** and **Example-Based Training** to distinguish between genuine communication and malicious fraud.

* **Dynamic Pattern Matching:** Trained on diverse "SAFE" vs "SCAM" datasets, including genuine bank alerts, Blue Dart delivery codes, and verified marketing headers like "VA-onTira".
* **Contextual Urgency Analysis:** The system distinguishes between "Marketing/Personal Information" and "Malicious Pressure." If a message lacks a forced "Call to Action" or immediate financial threat, it is prioritized as SAFE.
* **Zero-Tolerance Rules:** Any request for OTP sharing or instructions to call a personal mobile number for "official" or "emergency" bank/utility reasons is instantly flagged as a SCAM.
* **The Poison Pill Logic:** A suspicious link (bit.ly/ngrok) or a personal mobile sender pretending to be an official entity will override safe keywords and trigger the Honeypot.

### 2. Mrs. Higgins Agent (The Sword)
Once a scam is confirmed, the agent employs the **"Columbo Method"** to extract data:

* **Context-Aware Mirroring:** She reads the specific scam context and reacts humanly (e.g., panicking over a "blocked" pension) to lower the scammer's guard.
* **Strategic Failure:** She purposefully fails to click links, forcing the scammer to provide alternative, traceable payment handles (UPI/Bank) to "help" her.
* **Intelligence Extraction:** Every interaction is scanned in real-time to capture Bank Accounts, UPI IDs, Phishing Links, and Phone Numbers for reporting.

## Evaluation & Reporting
* **Automatic Reporting:** Intelligence is formatted into the required JSON payload structure.
* **Real-time GUVI Integration:** Automatically triggers a POST request to the endpoint upon data extraction.
* **Stateless Persistence:** Uses unique Session IDs (UUIDs) to track interactions.

## Tech Stack
* **Backend:** FastAPI / Uvicorn (Python)
* **AI Engine:** Llama-3.3-70b (via Groq Cloud)
* **Deployment:** Render / GitHub
* **Environment Security:** Secure handling of API Keys via OS-level Environment Variables.