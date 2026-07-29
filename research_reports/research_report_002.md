# Project Genesis Research Report

**Created:** 2026-07-25 23:24:29

**Prepared by:** Research AI

**Target audience:** small retail shops struggling with inventory management

**Status:** Preliminary and unvalidated

---

## Important Notice

This report was generated using AI reasoning and existing company context.

It does not contain verified live market research unless clearly stated.

Customer interviews and external validation are required before development begins.

---

**To:** Harshit (Founder, Project Genesis)  
**From:** Research AI Worker  
**Subject:** 3 AI Product Hypotheses for Small Retail Inventory Management  

Following our Constitution—specifically **Principle 1 (Profit First)** and **Principle 2 (Customer Obsession)**—I have researched and designed three distinct AI product hypotheses targeting small retail shop owners struggling with inventory management. 

Each of these ideas is structured to solve a highly painful, daily problem for local shop owners with minimal technical friction, aiming for high profit potential with low development costs.

---

### #UNVALIDATED HYPOTHESIS 1: ShelfEye AI

* **Product Name:** ShelfEye AI
* **Customer Problem:** Small retail shop owners (e.g., local grocers, boutique owners) spend hours every week manually counting stock on shelves and in backrooms to identify what is running low, which leads to human error and stockouts.
* **Proposed AI Solution:** A mobile app where the store owner simply takes a quick video or photo of their shelves. A lightweight computer vision AI analyzes the image, identifies the items, counts them, and instantly flags low-stock or misplaced items compared to their baseline shelf layout.
* **Why Customers May Pay:** It saves them 3–5 hours of manual, tedious labor per week and prevents lost sales caused by out-of-stock items they didn't realize were empty.
* **Difficulty Score (out of 10):** **7/10** (Training computer vision to accurately recognize varied packaging in poor lighting conditions can be challenging, though existing open-source models lower this barrier).
* **Profit Potential Score (out of 10):** **8/10** (High perceived value; can be sold as a monthly software-as-a-service subscription).
* **Main Risk:** Messy shelves, overlapping products, or poor camera quality in local shops could cause inaccurate counts, leading to user frustration and loss of trust.
* **Validation Required:** Interview 10 local shop owners to see if they would allow us to test a basic, manual photo-based mock-up of their shelves, and check if they currently lose money due to unrecognized stockouts.

---

### #UNVALIDATED HYPOTHESIS 2: WhatsApp BillParse AI

* **Product Name:** BillParse AI
* **Customer Problem:** When new stock arrives, small retailers must manually type product names, quantities, and wholesale prices from paper distributor invoices into their ledger or basic spreadsheets. This process is slow, boring, and prone to typing errors.
* **Proposed AI Solution:** A simple WhatsApp-based AI assistant. The retailer snaps a photo of any physical invoice or bill and sends it to the BillParse WhatsApp number. An AI Document Parser (using OCR and LLMs) instantly extracts the items, quantities, and costs, automatically updating their digital inventory ledger.
* **Why Customers May Pay:** Zero learning curve (they already use WhatsApp). It eliminates manual data entry, turning a 20-minute daily chore into a 5-second photo snap.
* **Difficulty Score (out of 10):** **3/10** (Very low. Uses existing mature OCR APIs and LLM parsing prompts, requiring minimal backend infrastructure).
* **Profit Potential Score (out of 10):** **9/10** (Extremely cheap to build and run, with highly visible, immediate time-saving value for the merchant).
* **Main Risk:** Highly non-standard, handwritten, or smudged paper invoices from local distributors might fail to parse accurately.
* **Validation Required:** Collect 20 sample paper invoices from local shops to test if standard AI vision APIs can extract the data with 95%+ accuracy without manual coding.

---

### #UNVALIDATED HYPOTHESIS 3: PredictStock AI

* **Product Name:** PredictStock AI
* **Customer Problem:** Small retailers struggle with cash flow because they over-purchase slow-moving stock (dead stock) and under-purchase fast-moving items, relying entirely on "gut feeling" rather than data.
* **Proposed AI Solution:** A simple, web-based analytics dashboard. The retailer uploads their historical sales CSV or links their basic Point-of-Sale (POS). A predictive AI analyzes sales trends, seasonal patterns, and local events to give them a weekly "Smart Buy List" showing exactly what to order and what to hold off on.
* **Why Customers May Pay:** Directly improves their bottom line by freeing up locked cash from dead inventory and maximizing revenue on high-demand products.
* **Difficulty Score (out of 10):** **5/10** (Requires clean time-series prediction models, but data ingestion must be kept dead simple for non-tech-savvy users).
* **Profit Potential Score (out of 10):** **8/10** (Strong ROI-driven pitch: "We save you more money in dead stock than our subscription costs").
* **Main Risk:** Small retailers often do not maintain clean, digital historical sales data, making prediction models difficult to train.
* **Validation Required:** Speak to local shop owners to find out how they currently decide what to order, and check if they have at least 3-6 months of digital sales records (from a POS, digital ledger, or Excel).

---

### Recommendation for Next Steps (Principle 1 & Principle 6)
In accordance with **Principle 6 (Honest Decisions)**, we must assume we do not know which product will succeed until we test. 

However, based on **Principle 1 (Profit First - Cheapest and Fastest)**, **BillParse AI** presents the lowest difficulty (3/10) and highest immediate leverage. It requires no complex app development (leveraging WhatsApp) and solves a universal friction point (manual data entry). 

I recommend we design a simple WhatsApp-based validation test for **BillParse AI** first.

---

## Current Decision

No product has been approved automatically.

Final product selection requires review and approval from Harshit, Founder of Project Genesis.
