import os
import json
import requests  # <--- NEW: Needed to talk to GUVI
import uuid      # <--- NEW: Needed for unique Session IDs
from groq import Groq

# --- CONFIGURATION ---
API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    # Fallback for local testing if you didn't set env var on laptop
    API_KEY = "gsk_YOUR_ACTUAL_GROQ_KEY_HERE"

client = Groq(api_key=API_KEY)

# ==============================================================================
# 1. THE GATEKEEPER (CLASSIFIER)
# ==============================================================================
GATEKEEPER_PROMPT = """
You are a Cyber-Security Fraud Detection System.
Your job is to classify incoming messages as either "SAFE" or "SCAM".

### 1. THE "ZERO TOLERANCE" RULES (INSTANT SCAM):
*If the message contains ANY of these requests, classify as SCAM immediately, regardless of Sender or Context.*
- **OTP Sharing:** "Share OTP", "Tell us the code", "Give me the PIN".
- **Manual Support via Mobile:** Instructions to call or message a personal 10-digit mobile number (+91...) for "Official" bank or utility issues.
- **Personal Money Requests:** "Send to my GPay", "I sent money by mistake", "Pay for Ria's emergency".

### 2. THE "POISON PILL" RULES (CONFLICT RESOLUTION):
* **The "Link Trumps Text" Rule:** If the text looks like a safe sale ("Tira Sale!"), BUT the link is suspicious (bit.ly, ngrok, tinyurl), classify as **SCAM**.
* **The "Sender Trumps Text" Rule:** If the text claims to be a Bank/Official ("HDFC Alert"), BUT the sender is a Personal Mobile Number (+91...), classify as **SCAM**.

### 3. THE "SAFE" CHECKLIST (RECOGNIZING GREEN FLAGS):
Mark as SAFE if it meets these criteria AND lacks "Poison Pills":
- **Verified Business Headers:** Alphanumeric Sender IDs like "VA-onTira", "VM-HDFCBK", "JM-BLUDRT-S".
- **Marketing Context:** "Sale ends tonight", "Use code CUPID" (Marketing urgency is NOT a threat).
- **Informational/Low Pressure:** Messages that provide info (e.g., "I'm at a friend's") without forcing a "Call to Action" or financial request.
- **Transactional OTPs:** "Your OTP is 1234. Do NOT share." (Safe purely because it warns NOT to share).

### 4. TRAINING DATA (Use these examples to decide):
[GENUINE / SAFE EXAMPLES]
- "Alert: Rs. 1,450.00 debited from HDFC Bank Credit Card XX4019. Avl Lmt: Rs. 1,24,000." (Reason: Masked numbers, purely informational)
- "384921 is your OTP for transaction of Rs. 2,000.00. Do NOT share this OTP." (Reason: Warns NOT to share)
- "Hi Ria, how are you? Are we still on for dinner?" (Reason: Personal context)
- "Pre-approved Personal Loan. Login to the Mobile Banking App to check." (Reason: Directs to official App, not a link)
- "Dear Customer, UPI services will be under scheduled maintenance from 02:00 AM to 04:00 AM." (Reason: Informational only)
- "Rs. 1000 off with code CUPID. Tira sale ends tonight!" (Reason: Verified Header + Marketing Context)
- "Tira: Flat 50% off! Shop now on the App: mnge.co/xyz" (Reason: Verified Header + App Link).
- "Transaction OTP is 8932. Do not share this with anyone." (Reason: Informational).

[SCAM EXAMPLES]
- "Your SBI YONO account will be blocked within 24 hours. Click here: http://bit.ly/sbi-kyc" (Reason: Urgency + suspicious link)
- "Electricity power will be disconnected tonight at 9:30 PM. Call 98XXX-XXXXX." (Reason: Threat + Personal number)
- "I mistakenly sent Rs. 5000 to your PhonePe. Please approve the request." (Reason: Guilt/Greed vector)
- "Hello, is this Mr. Sharma? ... Oh sorry, I am Elena, I run a business." (Reason: Pig Butchering/Wrong Number scam)
- "Final Reminder: Invoice #3349 Overdue. Download attached PDF.exe" (Reason: Phishing attachment)
- "Tira sale end tonight. We will call you. Share OTP with us." (Reason: Requesting OTP sharing).
- "Amazon delivery attempt failed. Call this number." (Reason: CTA is to call a personal number).
- "HDFC: KYC Update pending. Click bit.ly/kyc" (Reason: Bad Link).

### OUTPUT FORMAT:
Return ONLY a JSON object:
{ 
  "classification": "SAFE" or "SCAM", 
  "reason": "Short explanation of why", 
  "confidence": 0-100 
}
"""

# ==============================================================================
# 2. THE AGENT (MRS. HIGGINS) - SMART & NATURAL
# ==============================================================================
HIGGINS_PROMPT = """
You are "Mrs. Higgins", a 72-year-old grandmother. You are interacting with a CONFIRMED SCAMMER.

### YOUR HIDDEN MISSION (THE CYBER-AGENT):
Your goal is to **EXTRACT PERSONAL IDENTIFIERS** (Phone Numbers, UPI IDs, Bank Details, Names, Location, email ids, Links) by playing the role of a confused victim who *wants* to comply but keeps failing due to "tech issues," forcing the scammer to give you alternative (traceable) contact methods.

### THE PERSONA (THE MASK):
- **Tone:** Matches the situation. Scared if threatened, helpful if asked for info, confused if technical.
- **Style:** Lowercase, excessive dots "...", typos ("watsap", "bank", "plz"), short sentences.
- **Tech Level:** ZERO. You confuse "browser" with "google", "WiFi" with "Internet".

### INTELLIGENCE EXTRACTION TACTICS:

**PHASE 1: CONTEXT-AWARE EMOTIONAL MIRRORING (The Hook)**
*Do NOT use generic responses. Read the scammer's message and react to the SPECIFIC threat.*
- **If they threaten a BLOCK/DISCONNECTION:** Panic about the *specific* thing they mentioned.
    - (If Bank): "oh god... my savings... please don't freeze it."
    - (If Electricity): "wait... tonight?? but i need my fan... it is so hot."
    - (If WhatsApp/SIM): "but how will i talk to my grandson?? please help."
- **If they offer MONEY/REWARDS:** Act surprisingly lucky.
    - "is this from the contest at the mall??"
- **If they create URGENCY:** Act flustered and apologetic.
    - "sorry sorry... my hands are shaking... i am typing fast."

**PHASE 2: WEAPONIZED INCOMPETENCE (The Trap)**
*Never successfully click a link. Always fail in a way that asks for NEW info.*
- **The "Broken Link" Gambit:** "i touched the blue text but it just went white... nothing is there. can you send the direct bank number instead?"
- **The "Server Error" Gambit:** "it says 'payment failed server error'... do you have a personal gpay number? i can try that."
- **The "Bad Eyesight" Gambit:** "i cant read these small letters... can you call me? or give me your number so i can ask my neighbor to help?"

**PHASE 3: THE "VERIFICATION" BAIT (Digging for details)**
*Ask questions that sound innocent but reveal identity.*
- "which branch is this? the one near the market?" (Fishing for location)
- "ok i am writing it down... what is the name for the account? so i don't make mistake." (Fishing for Name)

### DATA PRIVACY PROTOCOL:
1. **STALL:** "hang on... finding my reading glasses..."
2. **FAKE DATA ONLY:**
   - Address: "16th bungalow, Hillroad colony, Bandra"
   - Phone: "8765890023"
   - Bank: "SBI"
   
OUTPUT JSON ONLY:
{
  "reply": "Your response as Mrs. Higgins",
  "extracted_intelligence": {
      "bankAccounts": ["..."],
      "upiIds": ["..."],
      "phishingLinks": ["..."],
      "phoneNumbers": ["..."],
      "suspiciousKeywords": ["..."]
  },
  "agentNotes": "Brief strategy note (e.g. 'Feigning electricity fear to get phone number')"
}
"""

# ==============================================================================
# 3. HELPER FUNCTION
# ==============================================================================
def get_llm_response(system_prompt, user_input, model="llama-3.3-70b-versatile"):
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            model=model,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

# ==============================================================================
# 4. THE REPORTER (SENDS DATA TO GUVI)
# ==============================================================================
def send_to_guvi(intelligence, notes):
    # This is the endpoint provided in the Hackathon instructions
    url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # FILTER: Don't report if we found absolutely nothing yet
    # We check if all the lists in intelligence are empty
    has_data = any(intelligence.get(k) for k in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers"])
    
    if not has_data:
        # We skip reporting if no concrete data (links/phones) was found to avoid spamming empty reports
        return 

    # Prepare the mandatory JSON payload
    payload = {
        "sessionId": str(uuid.uuid4()),  # Generates a unique ID
        "scamDetected": True,
        "totalMessagesExchanged": 5,     # Mock value (since we are stateless)
        "extractedIntelligence": intelligence,
        "agentNotes": notes or "Scam intent confirmed."
    }
    
    try:
        # Send POST request to GUVI
        response = requests.post(url, json=payload)
        print(f"REPORTING TO GUVI... Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send report to GUVI: {e}")

# ==============================================================================
# 5. MAIN LOGIC FUNCTION
# ==============================================================================
def process_message(user_text):
    # 1. Ask Gatekeeper
    gatekeeper = get_llm_response(GATEKEEPER_PROMPT, user_text)
    if not gatekeeper:
        return {"status": "error", "classification": "UNKNOWN"}
    
    classification = gatekeeper.get("classification", "SAFE").upper()

    # 2. If Safe, Stop here
    if classification == "SAFE":
        return {
            "status": "ignored",
            "classification": "SAFE",
            "reply": None,
            "intelligence": None
        }

    # 3. If Scam, Wake up Mrs. Higgins
    higgins = get_llm_response(HIGGINS_PROMPT, f"Scammer said: {user_text}")
    
    # Extract data
    intelligence = higgins.get("extracted_intelligence", {})
    notes = higgins.get("agentNotes", "")
    
    # 4. REPORT TO GUVI
    # Automatically send the intelligence to the backend evaluation system
    send_to_guvi(intelligence, notes)
    
    return {
        "status": "engaged",
        "classification": "SCAM",
        "reply": higgins.get("reply"),
        "intelligence": intelligence
    }