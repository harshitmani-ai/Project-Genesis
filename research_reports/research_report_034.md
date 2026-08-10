# Project Genesis Research Report

**Created:** 2026-08-10 13:26:06

**Prepared by:** Research AI

**Target audience:** Design the end-to-end system architecture for DentalReview AI Version 1, including component interaction, backend services, and third-party integrations.

**Status:** Preliminary and unvalidated

---

## Important Notice

This report was generated using AI reasoning and existing company context.

It does not contain verified live market research unless clearly stated.

Customer interviews and external validation are required before development begins.

---

# Research Report: End-to-End System Architecture & Preliminary Product Hypotheses for DentalReview AI Version 1

**Role:** Research AI Worker  
**Project:** Project Genesis  
**Target Audience:** Independent Dental Practices and Small Dental Clinics  
**Core Mission:** Aligning with **Principle 1 (Profit First)**, **Principle 2 (Customer Obsession)**, and **Principle 6 (Honest Decisions)** of the Project Genesis Constitution to design a profitable, high-value AI product for local dental clinics.

---

## Executive Summary

In compliance with our company constitution, this report delivers two key components for **DentalReview AI Version 1**:
1. **End-to-End System Architecture:** A comprehensive technical blueprint detailing component interaction, backend services, database structures, and third-party integrations required to build DentalReview AI V1 efficiently and securely.
2. **Three Preliminary Product Hypotheses:** A detailed breakdown of three distinct product angles under the DentalReview AI umbrella, structured with honest assessments, difficulty scores, and validation requirements.

*Disclaimer: In strict accordance with **Principle 6 (Honest Decisions)**, all technical specifications, operational metrics, difficulty scores, and customer pain points below are **unvalidated hypotheses and design projections**. No live production code or external API production keys have been deployed yet. Every assumption must be verified during MVP testing.*

---

# Part 1: End-to-End System Architecture (DentalReview AI Version 1)

The architecture for DentalReview AI Version 1 is designed following the **Profit First** and **Lean Startup** principles. It minimizes external vendor costs, utilizes managed serverless infrastructure, and maintains strict data separation to ensure security and scalability.

```
+-----------------------------------------------------------------------------------+
|                              DENTALREVIEW AI CLIENTS                              |
|          [Dental Practice Manager Dashboard]  [Patient Mobile Review View]        |
+-----------------------------------------------------------------------------------+
          | (HTTPS / REST API / WebSockets)                    | (Secure HTTPS Link)
          v                                                    v
+-----------------------------------------------------------------------------------+
|                          API GATEWAY & LOAD BALANCER                              |
|                    (AWS API Gateway / Vercel Edge Routing)                        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                              BACKEND APPLICATION CORE                             |
|               (Node.js / Express or Python FastAPI Serverless Functions)          |
|                                                                                   |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | Auth & RBAC Module |  | Review Sync Engine |  | AI Sentiment & Reply Engine |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
+-----------------------------------------------------------------------------------+
          |                        |                              |
          v                        v                              v
+-------------------+    +--------------------+        +----------------------------+
| PRIMARY DATABASE  |    | GOOGLE BUSINESS    |        | LLM PROVIDER API           |
| (PostgreSQL /     |    | PROFILE API        |        | (OpenAI GPT-4o-mini /      |
| Supabase + RLS)   |    | (OAuth 2.0 /       |        |  Anthropic Claude 3.5)     |
+-------------------+    |  Review Sync)      |        +----------------------------+
                         +--------------------+
```

---

## 1. System Component Breakdown

### A. Frontend Layer
* **Technology Stack:** Next.js (React) hosted on Vercel or Netlify.
* **Purpose:** Provides the Practice Manager Dashboard for viewing incoming reviews, managing AI-generated reply drafts (approve/edit/reject), and configuring clinic settings.
* **Key Interfaces:**
  * Review Feed & Status Tracker (Pending Approval, Posted, Flagged).
  * One-Click Approval & Edit Modal.
  * Basic Analytics View (Average rating trend, response rate, review volume).

### B. Backend Application Services
* **Technology Stack:** Node.js (TypeScript) with Express or Python (FastAPI) running as serverless functions (AWS Lambda or Vercel Serverless).
* **Core Microservices / Modules:**
  1. **Authentication & Multi-Tenant RBAC Module:** Handles secure staff logins (Google OAuth / Magic Link) and enforces clinic-level tenant isolation.
  2. **Google Business Profile (GBP) Sync Engine:** Periodically polls or receives webhooks from Google APIs to fetch new reviews and push approved replies.
  3. **AI Sentiment & Reply Engine:** Processes incoming review text, evaluates patient sentiment, checks against healthcare privacy guardrails (e.g., HIPAA compliance parameters), and generates warm, professional draft responses.

### C. Data Persistence Layer
* **Primary Database:** PostgreSQL (managed via Supabase or AWS RDS) with Row-Level Security (RLS) enabled.
* **Schema Design:**
  * `Clinics`: Stores practice profile, Google location ID, timezone, subscription status, and brand voice preferences.
  * `Users`: Stores manager/staff credentials, roles, and clinic associations.
  * `Reviews`: Stores review ID, author name, rating, raw review text, sentiment classification (`Positive`, `Neutral`, `Negative`), and moderation status (`Pending`, `Approved`, `Flagged`).
  * `Audit_Logs`: Tracks who approved/edited which reply and when (essential for healthcare accountability).

### D. Third-Party Integrations
1. **Google Business Profile API (OAuth 2.0):** Required for reading public reviews and posting authorized responses.
2. **LLM Provider API (OpenAI GPT-4o-mini / Anthropic Claude 3.5 Sonnet):** Used for fast, cost-effective sentiment analysis and response generation.
3. **Stripe API:** Handles SaaS subscription billing, trial management, and invoicing.
4. **Twilio / SendGrid (Optional V1 Extension):** For automated SMS review request triggers post-visit.

---

# Part 2: Three Preliminary Product Hypotheses

In alignment with **Principle 6 (Honest Decisions)**, below are three distinct product hypotheses under the **DentalReview AI** umbrella. Each explores a specific angle of the dental reputation management market.

---

## Hypothesis 1: DentalReview AI — HIPAA-Compliant Review Auto-Responder

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** DentalReview AI — HIPAA-Compliant Auto-Responder
2. **Customer Problem:** Dental practices need to reply to Google reviews to boost local SEO. However, they are bound by healthcare privacy laws (e.g., HIPAA). If a patient leaves a review saying, *"Dr. Smith did an amazing job on my root canal!"* and the clinic replies, *"Thank you, we were glad to help with your root canal!"*, they have committed a privacy violation by confirming treatment details. Consequently, staff either write generic, robotic replies or avoid replying entirely.
3. **Proposed AI Solution:** A lightweight dashboard where incoming Google reviews are processed by an LLM trained on strict privacy guidelines. The AI drafts warm, personalized, yet 100% compliant responses (never confirming patient status or clinical procedures) and presents them to the office manager for one-click approval and posting.
4. **Why Customers May Pay:** Eliminates compliance anxiety while actively boosting Google Map Pack rankings through consistent review engagement, driving new patient inquiries.
5. **Difficulty Score:** `3 / 10` (Standard web app with Google OAuth, LLM API prompting, and Google Business Profile API integration).
6. **Profit Potential Score:** `8 / 10` (High recurring value at $49–$99/month, low operating cost per tenant).
7. **Main Risk:** AI hallucination causing a compliance slip if guardrails are not rigorously tested.
8. **Validation Required:** Interview 10 dental practice managers to confirm if fear of privacy violations stops them from replying to patient reviews.

---

## Hypothesis 2: DentalReview AI — AutoPulse (Post-Visit Review Funnel & Sentiment Interceptor)

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** DentalReview AI — AutoPulse
2. **Customer Problem:** Dental receptionists are overwhelmed with patient check-ins and insurance verification, meaning post-visit review requests are rarely sent manually. Meanwhile, unhappy patients readily leave negative reviews unprompted, skewing ratings.
3. **Proposed AI Solution:** An automated SMS/email follow-up trigger sent shortly after patient checkout. It evaluates patient sentiment; positive feedback is directed instantly to public Google/Yelp links, while negative or neutral feedback is intercepted privately so the practice manager can resolve issues internally.
4. **Why Customers May Pay:** Increasing 5-star review volume directly increases local search visibility and patient acquisition, paying for itself if it captures just one new procedure per quarter.
5. **Difficulty Score:** `4 / 10` (Requires Twilio/SendGrid API integration combined with automated scheduling triggers).
6. **Profit Potential Score:** `9 / 10` (Extremely sticky SaaS product once embedded into daily front-desk workflows).
7. **Main Risk:** Deliverability issues with SMS carrier filtering or reluctance of clinics to adopt new communication tools.
8. **Validation Required:** Survey 10 independent dental clinics on their current review request workflow and willingness to use automated SMS follow-ups.

---

## Hypothesis 3: DentalReview AI — Competitor Pulse (Local Dental SEO & Review Benchmarker)

### [UNVALIDATED HYPOTHESIS]

1. **Product Name:** DentalReview AI — Competitor Pulse
2. **Customer Problem:** Dental practice owners know they have local competitors, but they lack visibility into how their Google rating velocity, review sentiment, and keyword response rates compare against other clinics in their zip code.
3. **Proposed AI Solution:** A weekly automated intelligence report that aggregates public Google review data for a dental practice and its top 5 local competitors. The AI highlights rating gaps, identifies common patient complaints about competitors (e.g., long wait times or billing confusion), and suggests marketing angles for the practice.
4. **Why Customers May Pay:** Gives practice owners actionable marketing insights without requiring them to hire an expensive SEO agency.
5. **Difficulty Score:** `3 / 10` (Web scraping public Google Maps data via APIs or structured scrapers combined with LLM summarization).
6. **Profit Potential Score:** `7 / 10` (Good tier add-on feature, though slightly lower standalone utility than active review response automation).
7. **Main Risk:** Google API rate limits or structural changes to public map listings breaking scraper feeds.
8. **Validation Required:** Ask clinic owners if they regularly track competitor review ratings and whether a weekly automated competitor brief is worth $29/month.

---
*Report compiled by Research AI Worker for Project Genesis.*

---

## Current Decision

No product has been approved automatically.

Final product selection requires review and approval from Harshit, Founder of Project Genesis.
