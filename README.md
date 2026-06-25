


Markdown
# 🏗️ BlueprintIQ - Local Execution Guide

BlueprintIQ is an enterprise-grade document intelligence engine designed to extract and organize construction materials from complex structural plans (PDFs, BOQs, etc.) and generate stage-wise procurement schedules. 

To ensure maximum data privacy and zero hallucination, this pipeline utilizes localized open-source machine learning models (IBM Docling for layout parsing and PaddleOCR for visual fallback) rather than cloud APIs. 

**Important Note on Execution:** Because these heavy machine-learning layout models require a minimum of 4GB of RAM to process document matrices, they exceed standard free-tier cloud container limits (which typically cap at 512MB and cause Out-Of-Memory crashes). Therefore, this architecture is designed to be evaluated and run locally for maximum stability and speed.

Follow this step-by-step guide to run the complete end-to-end architecture on your local machine.

---

## 🛠️ Prerequisites

Before you begin, ensure your system has the following installed:
1. **Python:** Version 3.11 or higher.
2. **Node.js:** Version 20 or higher.
3. **Git:** To clone the repository.
4. **C++ Build Tools:** Required for installing certain Python machine learning dependencies (like PaddleOCR).

---

## 🚀 Step 1: Clone the Repository

Open your terminal or command prompt and clone the project to your local machine:

```bash
git clone [https://github.com/](https://github.com/)[your-username]/blueprintiq.git
cd blueprintiq


(Replace [your-username] with your actual GitHub username)
⚙️ Step 2: Configure the Backend Environment
The backend relies on the CHATGPT API for its reasoning engine. We must set this up securely.
Navigate to the Backend Directory:
Bash
cd backend


Create the Environment File:
Create a new text file named .env in the root of the backend folder (path: blueprintiq/backend/.env).
Add Your Configuration Variables:
Open the .env file in your code editor and paste the following, replacing the placeholder with your actual Gemini API key (which usually starts with AIzaSy...):
Code snippet
# ==============================================================================
# BLUEPRINTIQ: LOCAL BACKEND ENVIRONMENT CONFIGURATION (.env)
# ==============================================================================

# --- Storage Infrastructure ---
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
DATABASE_PATH=blueprintiq.db

# --- Vision & Layout Pipeline ---
# Set to True to initialize PaddleOCR for scanned/raster document parsing fallback
ENABLE_LOCAL_VISION_FALLBACK=True
VISION_ENGINE_TYPE=paddleocr

# --- Document Extraction Pipeline ---
DOCLING_TABLE_MODE=accurate
DOCLING_TIMEOUT_SECONDS=300
DOCLING_OCR_LANG=en

# --- Reasoning & Synthesis Engine (LLM) ---
# Paste your active Gemini or OpenAI API Key directly below (No spaces or quotes)
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4o

# --- Application Security Boundaries ---
APP_NAME=BlueprintIQ
MAX_UPLOAD_MB=50
LOG_LEVEL=info


🧠 Step 3: Install Backend Dependencies & Start Server
Now we will install the machine learning libraries (this may take a few minutes as it downloads the model weights) and boot the API.
Ensure you are in the backend directory:
Bash
# You should be in blueprintiq/backend

Install Python Dependencies:
Bash
pip install -r requirements.txt


Start the FastAPI Server:
Bash
uvicorn app.main:app --reload --port 8000

Keep this terminal window open. You should see a message indicating the application startup is complete and listening on http://127.0.0.1:8000.
🖥️ Step 4: Configure & Start the Frontend
With the backend running, we now need to boot the Next.js user interface.
Open a NEW Terminal Window/Tab.
Navigate to the Frontend Directory:
Bash
cd blueprintiq/frontend


Create the Frontend Environment File:
Create a new text file named .env.local in the root of the frontend folder (path: blueprintiq/frontend/.env.local).
Define the Local API Route:
Add the following line to .env.local so Next.js knows where to send data:
Code snippet
NEXT_PUBLIC_API_BASE_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)


Install Node Dependencies:
Bash
npm install


Start the Next.js Development Server:
Bash
npm run dev


🎉 Step 5: Run the Application
Open your web browser.
Navigate to: http://localhost:3000
Drop any structural Bill of Quantities (BOQ) PDF or construction specification document into the upload zone to test the local extraction engine!
