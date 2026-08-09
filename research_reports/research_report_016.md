# Project Genesis Research Report

**Created:** 2026-08-09 18:38:18

**Prepared by:** Research AI

**Target audience:** Approve Hypothesis 1: DentiShield AI. Freeze the MVP scope. Create a complete UI/UX design specification for every screen. Do not write code.

**Status:** Preliminary and unvalidated

---

## Important Notice

This report was generated using AI reasoning and existing company context.

It does not contain verified live market research unless clearly stated.

Customer interviews and external validation are required before development begins.

---

# RESEARCH WORKER REPORT: PROJECT GENESIS
**To:** Harshit (Founder)  
**From:** Research AI Worker  
**Date:** August 9, 2026  
**Subject:** Approval of Hypothesis 1 (DentiShield AI), MVP Scope Freeze, Complete UI/UX Specification, and Dental Clinic Product Hypotheses  

---

## Part 1: Constitutional Alignment & Executive Summary

In alignment with **Principle 1 (Profit First)** and **Principle 2 (Customer Obsession)** of the Project Genesis Constitution, we are narrowing our operational focus. Rather than building over-complicated, broad platforms, we are freezing a hyper-focused, high-margin MVP for **DentiShield AI**. 

In keeping with **Principle 6 (Honest Decisions)**, we state clearly that the product hypotheses presented below are **unvalidated hypotheses**. We have not performed live database integration tests or real-world scraping on dental practice patterns for this exact cohort. The metrics, difficulty ratings, and risk profiles represent analytical estimations designed to guide safe, low-risk validation.

---

## Part 2: Product Hypotheses (Exactly 3)

The following three preliminary hypotheses target the local dental clinic market.

### [UNVALIDATED HYPOTHESIS 1]
### 1. DentiShield AI — Predictive Appointment Retention & Auto-Fill
*   **Product Name:** DentiShield AI
*   **Customer Problem:** No-shows and last-minute cancellations cost the average dental clinic thousands of dollars per month in idle staff time and unutilized operational chairs. Office managers waste valuable phone time manually calling waitlists to patch schedule holes.
*   **Proposed AI Solution:** A lightweight software layer that analyzes historical patient attendance patterns and external variables (e.g., weather, traffic, appointment history) to flag patients with a high risk of no-showing. It automates hyper-personalized, conversational SMS confirmations. If a cancellation occurs, the AI immediately converses with waitlisted patients via SMS to secure a replacement booking without manual human intervention.
*   **Why Customers May Pay:** A single prevented no-show for a high-value procedure (e.g., crown, root canal) yields $800+ in retained revenue. At a monthly price of $49 to $99, the software pays for itself with its first successful auto-fill.
*   **Difficulty Score:** `6 / 10` (Requires integration with dental Practice Management Software (PMS) APIs or a simple CSV upload, alongside a conversational SMS pipeline).
*   **Profit Potential Score:** `9 / 10` (High ROI clarity for the buyer, highly repeatable SaaS model, low ongoing operational costs).
*   **Main Risk:** Legacy, on-premise Dental Practice Management Software (PMS) like older versions of Dentrix or Eaglesoft can be notoriously difficult to integrate with.
*   **Validation Required:** Interview 10 local dental office managers to confirm if late cancellations are their top daily frustration, and ask if they would permit an AI to text their waitlisted patients to book open slots.

---

### [UNVALIDATED HYPOTHESIS 2]
### 2. DentiScribe AI — Ambient Clinical Charting Assistant
*   **Product Name:** DentiScribe AI
*   **Customer Problem:** Dentists spend 1.5 to 2 hours at the end of every clinical day typing up patient progress notes, leading to administrative fatigue, clinical burnout, and reduced time spent treating patients.
*   **Proposed AI Solution:** A secure, ambient listening application run from a tablet or smartphone in the operatory. The AI captures the verbal dialogue between the dentist, assistant, and patient, filters out non-clinical small talk, and structures precise, compliant SOAP clinical notes ready to be reviewed, approved, and pasted into the patient's record.
*   **Why Customers May Pay:** Saves 10+ hours a week of clerical work, allowing the dentist to either go home on time or add one extra patient block per day, translating to thousands in additional weekly production.
*   **Difficulty Score:** `8 / 10` (Requires HIPAA-compliant data pipelines, high-accuracy speech-to-text, and fine-tuned LLM processing for specialized dental terminology).
*   **Profit Potential Score:** `8 / 10` (Dentists demonstrate high willingness to pay for clinical time-savers, with target pricing at $149–$249/month).
*   **Main Risk:** Stringent HIPAA compliance barriers, patient consent hesitations regarding room recording, and clinical accuracy liabilities.
*   **Validation Required:** Walk through a simulated transcript with 5 practicing dentists to see if the AI-generated output matches their clinical note requirements.

---

### [UNVALIDATED HYPOTHESIS 3]
### 3. DentalReview AI — Smart Local SEO & Reputation Booster
*   **Product Name:** DentalReview AI
*   **Customer Problem:** Dental practices rely heavily on local Google Maps search rankings to acquire new high-value cosmetic and implant patients. They struggle to gather Google reviews because patients forget to leave them, and manual reminders feel awkward or intrusive.
*   **Proposed AI Solution:** A post-appointment SMS feedback engine. After a successful treatment, the AI texts the patient a smart link. Based on a quick, single-tap experience rating, the AI generates a customized, draft review text highlighting what they liked. The patient simply taps "Copy" and is redirected to Google Maps to paste it in 3 seconds.
*   **Why Customers May Pay:** Rising to the top 3 spots on local Google search matches brings in an estimated 10–20 new patients per month without ad spend.
*   **Difficulty Score:** `3 / 10` (Very low technical risk; relies on standard SMS APIs and simple web frontends).
*   **Profit Potential Score:** `6 / 10` (High margin, but faces a highly saturated market with existing general reputation software players).
*   **Main Risk:** General CRM tools have basic built-in review request features, making differentiation on "AI" drafts critical.
*   **Validation Required:** Audit 30 local dental practices to see how many have fewer than 100 Google reviews, and pitch their managers on a tool guaranteed to double review velocity.

---

## Part 3: MVP Scope Freeze — DentiShield AI

To ensure compliance with **Principle 1 (Profit First)**, we are freezing the scope of the **DentiShield AI** Minimum Viable Product (MVP) to prevent feature creep and minimize upfront development costs.

### In-Scope Features (The Core Value Loop):
1.  **Dashboard Overview:** Displays high-risk appointments, recovered revenue, and active filling operations.
2.  **No-Show Risk Monitor (Calendar Integration):** Visual view flagging upcoming appointments as Low, Medium, or High risk of cancellation.
3.  **Conversational Waitlist Matching:** A manual-entry or CSV-uploaded waitlist where patients specify preferred days/times. The AI automatically matches cancellations to this list and coordinates booking via SMS.
4.  **Real-Time SMS Stream:** An interface showing the live, conversational interaction between the AI and the patient.
5.  **Simulated Integration / Settings Hub:** A configuration screen to upload patient schedules (via CSV) and input the clinic's basic operating hours.

### Out-of-Scope (Excluded from MVP):
*   Real-time direct database integration with on-premise legacy PMS systems (replaced by clean CSV upload/download for MVP).
*   Voice-call AI automation (strictly SMS-only for MVP).
*   Multi-clinic organization portals (single-location focus only).
*   Custom patient clinical histories or insurance verification.

---

## Part 4: UI/UX Design Specification (No Code)

This section provides complete visual layout structures and interaction maps for every screen in the DentiShield AI MVP.

### Screen 1: The Revenue Shield Dashboard (Main View)

#### 1. Visual Layout & Structure
*   **Header Bar:**
    *   Left side: "DentiShield AI" logotype in Deep Navy blue (`#1E293B`) with a secure shield icon badge.
    *   Right side: Active Location Dropdown (e.g., "Downtown Dental Care") and a User Profile avatar with a green "System Connected" status indicator.
*   **Sidebar Navigation (Left aligned, vertical, dark slate background):**
    *   Dashboard (Active state - highlighted in soft blue)
    *   Risk Calendar
    *   Smart Waitlist
    *   SMS Stream
    *   Settings
*   **Main Workspace Grid:**
    *   **Row 1: Key Performance Metrics (Three horizontal cards):**
        1.  *Revenue Saved Card:* Bold green text showing estimated recovered dollars (e.g., "$2,450 Saved This Month"). Subtext: "Based on 3 auto-filled crown appointments."
        2.  *Active Shield Rate Card:* Percentage indicator (e.g., "94% Confirm Rate"). Subtext: "+4.2% from last month."
        3.  *Queue Status Card:* Bold text (e.g., "3 High-Risk Today"). Subtext: "All protected by active SMS guards."
    *   **Row 2: Active Recovery Actions (Central wide panel):**
        *   A real-time progress monitor displaying active slot-filling operations. It displays a progress bar: `[Cancellation Detected] ──> [AI Scanning Waitlist] ──> [SMS Outbound Sent] ──> [Booking Confirmed]`.

#### 2. UI Elements
*   *Primary CTA:* "Run Manual Scan" button in Emerald Green (`#059669`) in the upper right.
*   *Alert Toast:* Top-center banner that slides in when a slot is successfully auto-filled: "🎉 AI successfully filled Friday 2:00 PM appointment with Patient Sarah Jenkins!"

#### 3. User Flows & Interaction
*   Clicking on the "Revenue Saved" card opens a modal explaining the math (Treatment Cost * Filled Appointments).
*   Hovering over any "Active Recovery Action" reveals the specific patient name and time slot currently being negotiated by the AI.

---

### Screen 2: No-Show Risk Monitor (Calendar View)

```
+----------------------------------------------------------------------------------+
| DentiShield AI  [ Downtown Dental Care v ]                  (Active) [User Profile]|
+----------------------------------------------------------------------------------+
| [D] Dashboard |  < October 2026 >                                 [+ Add Appt]   |
| [*] Calendar  |  +------------+------------+------------+------------+-----------+
| [W] Waitlist  |  | Mon 26     | Tue 27     | Wed 28     | Thu 29     | Fri 30    |
| [S] SMS Stream|  +------------+------------+------------+------------+-----------+
| [C] Settings  |  | 09:00 AM   | 09:00 AM   | 09:00 AM   | 09:00 AM   | 09:00 AM  |
|               |  | John Doe   | Jane Smith | [HIGH RISK]| Amy Cruz   | Bob Vance |
|               |  | [Low Risk] | [Med Risk] | Kyle Brown | [Low Risk] | [Low Risk]|
|               |  | (Confirmed)| (Pending)  | (No Reply) | (Confirmed)| (Confirmed|
+---------------+---------------+------------+------------+------------+-----------+
```

#### 1. Visual Layout & Structure
*   **Main Workspace:**
    *   A clean weekly calendar view grid (Monday through Friday, 8:00 AM to 5:00 PM).
    *   Each grid cell represents an appointment slot containing the patient's name, planned treatment (e.g., "Hygiene", "Crown"), and their AI-calculated Risk Badge.

#### 2. UI Elements
*   **Risk Badges (Color-coded pills):**
    *   *Red Pill [HIGH RISK]:* Assigned to patients with past no-shows or zero confirmation replies.
    *   *Yellow Pill [MODERATE RISK]:* Assigned to patients with average history or tentative booking indicators.
    *   *Green Pill [LOW RISK]:* Assigned to patients who consistently confirm early.
*   **Action Drawer:** Clicking on any calendar card slides open a panel from the right displaying:
    *   Patient contact history.
    *   AI risk factors breakdown (e.g., "Weather: Heavy Rain Forecasted", "History: No-showed twice in Q1").
    *   An "Override AI Guard" toggle switch.

#### 3. User Flows & Interaction
*   **Trigger:** Click on red-badged "Kyle Brown" slot.
*   **Result:** Right-side drawer slides open. The office manager sees that Kyle has not confirmed. A button labeled "Manually Trigger AI Re-Verify" is clicked.
*   **Feedback:** The status changes to "Texting Outbound Now" with a loading spinner icon.

---

### Screen 3: Smart Waitlist & Match Center

#### 1. Visual Layout & Structure
*   **Split Screen Layout (50/50 vertical division):**
    *   **Left Column (Active Waitlist Database):** A clean tabular list of patient profiles waiting for appointments.
    *   **Right Column (Auto-Fill Engine Log):** A chronological feed showing historical matches completed by the AI matching engine.

#### 2. UI Elements
*   **Waitlist Table Columns:**
    *   Patient Name
    *   Required Procedure (e.g., "Cleaning", "Filling")
    *   Preferred Days/Times (e.g., "Mornings only", "Tues/Thurs")
    *   Priority Ranking (Auto-scored based on time waiting and immediate availability).
*   *Action Button:* "Quick Add Patient to Waitlist" in Royal Blue (`#2563EB`) at the top of the table.

#### 3. User Flows & Interaction
*   **Add Patient Flow:**
    1.  User clicks "Quick Add Patient to Waitlist".
    2.  A centered pop-up modal appears with fields for Name, Phone, Procedure Type, and availability toggles.
    3.  User hits "Save". The table slides down and inserts the new patient at the calculated priority position.
*   **Match Simulation Flow:**
    *   A drag-and-drop mechanism allows the user to manually drag a waitlist patient onto an open slot on the calendar if they wish to bypass the automated AI queue.

---

### Screen 4: Conversational SMS Streams (Real-Time View)

```
+----------------------------------------------------------------------------------+
| DentiShield AI  [ Downtown Dental Care v ]                  (Active) [User Profile]|
+----------------------------------------------------------------------------------+
| [D] Dashboard | ACTIVE CHAT: Kyle Brown (High Risk)           | Waitlist Matches |
| [Calendar]    | +-------------------------------------------+ | +--------------+ |
| [Waitlist]    | | [AI] Hi Kyle, this is DentiShield on behalf| | | Auto-Fill:   | |
| [*] SMS Stream| | of Downtown Dental. Click to confirm your | | | Sarah Jenkins| |
| [C] Settings  | | appointment for tomorrow at 9:00 AM.      | | | confirmed for| |
|               | +-------------------------------------------+ | | Fri 2:00 PM  | |
|               | | [Kyle] Actually, I can't make it tomorrow | | +--------------+ |
|               | +-------------------------------------------+ |                  |
|               | | [AI] No problem! I can cancel that for    | |                  |
|               | | you. Would you like me to book you for    | |                  |
|               | | next Thursday at 10:00 AM instead?        | |                  |
+---------------+-----------------------------------------------+------------------+
```

#### 1. Visual Layout & Structure
*   **Two-Column Layout:**
    *   **Left Column (Conversational Thread List):** A list of all patient contacts with recent message history, ordered by most recent activity.
    *   **Right Column (Chat Window):** Detailed messaging view formatted like a standard SMS messenger interface, showing interactions between the AI assistant and the patient.

#### 2. UI Elements
*   **AI Tag Badge:** A small purple badge next to message bubbles sent by the AI, reading `[AI Assistant]`.
*   **Manual Intervention Banner:** A persistent top bar in the chat window reading: "AI is currently managing this conversation. [Take Over Chat]" in Amber Gold (`#D97706`).
*   **Input Box:** A text box at the bottom allowing manual typing if the office manager overrides the system.

#### 3. User Flows & Interaction
*   **Taking Control Flow:**
    1.  Office manager views an active AI conversation.
    2.  Manager clicks "Take Over Chat".
    3.  The amber banner turns red, reading: "Manual Override Active. AI is paused."
    4.  The input text box activates, letting the manager type a manual SMS response.
    5.  A "Resume AI Guard" button appears to return control to the system.

---

### Screen 5: Settings & Integration Hub

#### 1. Visual Layout & Structure
*   **Tabbed Interface Layout:**
    *   *Tab 1:* Practice Profile
    *   *Tab 2:* Calendar Sync (CSV / PMS)
    *   *Tab 3:* AI Customization (Tone & Timing)

#### 2. UI Elements
*   **Practice Profile Tab:** Input fields for practice address, office hours, and phone number.
*   **Calendar Sync Tab:**
    *   An upload area marked "Drag and drop your PMS schedule export (.CSV) here".
    *   A progress bar indicating upload status.
*   **AI Customization Tab:**
    *   *Timing Slider:* Set when the first confirmation SMS is sent (e.g., "24 hours before", "48 hours before").
    *   *Tone Selector Dropdown:* Choose from "Friendly & Direct", "Clinical & Formal", or "Warm & Conversational".

#### 3. User Flows & Interaction
*   **CSV Schedule Update Flow:**
    1.  Office manager exports schedule from legacy software to desktop.
    2.  Manager drags the CSV file onto the upload box.
    3.  A green checkmark appears: "124 appointments successfully mapped. 14 High-risk profiles updated."
    4.  The dashboard metrics automatically update in the background.

---

## Part 5: Next Action Proposal

Following **Principle 5 (Learn From Everything)**, our next step is low-risk validation. Before any design specs are passed to an engineer or any backend architectures are defined, we will present this non-coded layout structure and product hypothesis to real prospective buyers.

**Recommended Validation Test:**
We will contact 10 local dental practice office managers. We will explain the DentiShield concept and walk them through the screen descriptions. If at least 3 of them confirm they would upload daily schedule CSVs in exchange for automated waitlist fills at $49/month, we will officially move to phase-one system architecture.

---

## Current Decision

No product has been approved automatically.

Final product selection requires review and approval from Harshit, Founder of Project Genesis.
