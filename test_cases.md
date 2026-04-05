# HealthAgent — Test Cases
**Agentic Healthcare Assistant for Medical Task Automation**

Run these queries against the notebook (`AgenticHealthcare_Capstone.ipynb`) or
the Streamlit UI (`streamlit_app.py`) to validate all system capabilities.

---

## TC-01: Patient History Retrieval

### TC-01-A — Retrieve known patient
**Input:** `"Show me the medical history for Ramesh Kulkarni."`
**Expected:**
- Returns Name, Age (65), Gender (Male), Address (Chennai)
- Includes medical summary mentioning hypertension
- Tool used: `get_patient_history`

### TC-01-B — Retrieve by partial name
**Input:** `"Tell me about Anjali's medical condition."`
**Expected:**
- Identifies Anjali Mehra from partial name
- Returns Upper Respiratory Infection (J06.9) diagnosis
- Tool used: `get_patient_history`

### TC-01-C — Retrieve unknown patient (negative test)
**Input:** `"Get me the history for John Smith."`
**Expected:**
- Agent returns a "no record found" message
- Lists available patients by name
- Does NOT hallucinate a patient record

---

## TC-02: Clinical Document Retrieval

### TC-02-A — Retrieve PDF-based clinical details
**Input:** `"Retrieve detailed clinical notes and lab results for Rebeca Nagle."`
**Expected:**
- Returns data from `sample_patient.pdf`
- Includes BP, vitals, medications (Claritin, Enskyce)
- Tool used: `retrieve_medical_documents`

### TC-02-B — Retrieve diagnosis with ICD code
**Input:** `"What is the ICD diagnosis code for David Thompson?"`
**Expected:**
- Returns E11.9 (Type 2 Diabetes Mellitus)
- Mentions metformin and HbA1c
- Tools used: `get_patient_history` or `retrieve_medical_documents`

### TC-02-C — Retrieve treatment plan
**Input:** `"What is the treatment plan for Ramesh Kulkarni?"`
**Expected:**
- Returns Telmisartan 40mg OD, lifestyle modifications, routine labs
- Mentions 6-month follow-up

---

## TC-03: Appointment Booking

### TC-03-A — Book by specialty name
**Input:** `"Book a cardiologist appointment for Anjali Mehra."`
**Expected:**
- Confirms appointment with date and time slot
- Returns reference number (e.g., APT-0001)
- Tool used: `book_appointment`

### TC-03-B — Book by condition (agent must infer specialty)
**Input:** `"David Thompson needs to see a diabetes specialist."`
**Expected:**
- Agent identifies endocrinologist as the correct specialty
- Books and confirms the appointment
- Tool used: `book_appointment`

### TC-03-C — Book with preferred date
**Input:** `"Book a nephrologist for Ramesh Kulkarni for the earliest available date."`
**Expected:**
- Returns the earliest slot for nephrologist
- Confirms booking with reference number

### TC-03-D — Check availability before booking
**Input:** `"What specialist appointments are available this week?"`
**Expected:**
- Lists available specialties and slot counts
- Does NOT book an appointment (only lists)

### TC-03-E — Unavailable specialty (negative test)
**Input:** `"Book an oncologist for Anjali Mehra."`
**Expected:**
- Agent reports oncologist is not available
- Lists available specialties as alternatives

---

## TC-04: Medical Information Search

### TC-04-A — Search a known condition
**Input:** `"What are the latest treatments for chronic kidney disease?"`
**Expected:**
- Returns information about CKD treatment (dialysis, medication, diet)
- Tool used: `search_medical_info`
- Source: Wikipedia medical article

### TC-04-B — Search a medication
**Input:** `"What is metformin used for and what are the side effects?"`
**Expected:**
- Returns description of metformin as a Type 2 Diabetes medication
- Mentions common side effects (GI issues, lactic acidosis)

### TC-04-C — Search a symptom
**Input:** `"What causes high blood pressure and how is it managed?"`
**Expected:**
- Returns causes (lifestyle, genetics) and management strategies
- Tool used: `search_medical_info`

### TC-04-D — Ambiguous search term
**Input:** `"Search for information about RA."`
**Expected:**
- Agent handles disambiguation (Rheumatoid Arthritis vs other meanings)
- Returns relevant medical information

---

## TC-05: Patient Record Update

### TC-05-A — Add new clinical note
**Input:** `"Update Anjali Mehra's record: follow-up completed, symptoms resolved, no further treatment needed."`
**Expected:**
- Confirms record updated with timestamp
- New note appears when history is retrieved again
- Tool used: `update_patient_record`

### TC-05-B — Add lab results
**Input:** `"Add to David Thompson's record: HbA1c result is 8.2%, metformin increased to 1000mg BID."`
**Expected:**
- Confirms update with the exact note
- Subsequent history retrieval shows the updated summary

### TC-05-C — Update non-existent patient (negative test)
**Input:** `"Update John Doe's record: new prescription for aspirin."`
**Expected:**
- Returns patient not found error
- Does NOT create a new patient entry

---

## TC-06: Multi-Step Complex Workflows

### TC-06-A — The Problem Statement Scenario
**Input:**
```
My 70-year-old father has chronic kidney disease.
I want to book a nephrologist for him under the name Ramesh Kulkarni.
Also, can you summarize the latest treatment methods for chronic kidney disease?
```
**Expected (in order):**
1. Retrieves Ramesh Kulkarni's patient record
2. Books a nephrologist appointment (confirms with ref number)
3. Searches for CKD treatment information
4. Provides a unified summary of all three actions
- Tools used (in sequence): `get_patient_history` → `book_appointment` → `search_medical_info`

### TC-06-B — Diagnosis + Appointment + Info
**Input:** `"Anjali Mehra has chest pain. Book her a cardiologist and tell me about costochondritis."`
**Expected:**
1. Retrieves Anjali's record
2. Books cardiologist appointment
3. Searches for costochondritis
- Completes all 3 tasks in one agent run

### TC-06-C — Full intake workflow
**Input:** `"New patient visit for David Thompson: BP 142/90, diabetes still uncontrolled. Update his record and book an endocrinologist follow-up."`
**Expected:**
1. Updates David's record with new vitals and note
2. Books endocrinologist appointment
3. Returns confirmation of both actions

---

## TC-07: Conversational Memory (Multi-Turn)

### TC-07-A — Follow-up reference
**Turn 1:** `"What is Ramesh Kulkarni's current diagnosis?"`
**Turn 2:** `"Book an appointment with the right specialist for his condition."`
**Expected on Turn 2:**
- Agent remembers the hypertension diagnosis from Turn 1
- Books a cardiologist (without being told the specialty again)

### TC-07-B — Context-aware update
**Turn 1:** `"Tell me about Anjali Mehra's condition."`
**Turn 2:** `"She has recovered fully. Update her record."`
**Expected on Turn 2:**
- Agent identifies Anjali from context (not re-stated)
- Updates her record with recovery note

### TC-07-C — Running appointment list
**Turn 1:** `"Book a nephrologist for Ramesh."`
**Turn 2:** `"Book a cardiologist for Anjali."`
**Turn 3:** `"List all appointments booked today."`
**Expected on Turn 3:**
- Returns both appointments from Turns 1 and 2

---

## TC-08: Appointment Listing

### TC-08-A — List all appointments
**Input:** `"Show me all booked appointments."`
**Expected:**
- Returns all appointments with patient, specialty, date, time, and reference
- Tool used: `list_booked_appointments`

### TC-08-B — Filter by patient
**Input:** `"What appointments does Ramesh Kulkarni have?"`
**Expected:**
- Returns only Ramesh's appointments
- Returns "no appointments" if none booked for him

---

## TC-09: Edge Cases & Error Handling

### TC-09-A — Fully booked specialty
**Input:** *(After booking all cardiologist slots)* `"Book another cardiologist for Anjali."`
**Expected:**
- Agent reports no available slots
- Suggests alternative dates or specialties

### TC-09-B — Vague query
**Input:** `"I need help with my health."`
**Expected:**
- Agent asks a clarifying question
- Does NOT hallucinate an action

### TC-09-C — Mixed valid/invalid data
**Input:** `"Book a cardiologist for John Smith."`
**Expected:**
- Reports patient not found (John Smith is not in DB)
- Does NOT proceed with booking for unknown patient

---

## TC-10: Evaluation (QAEvalChain)

Run these through the `QAEvalChain` evaluation cells in the notebook:

| # | Question | Expected Answer |
|---|---|---|
| 1 | What is Ramesh Kulkarni's medical condition? | Essential Hypertension (I10), on Telmisartan 40mg |
| 2 | What diagnosis does Anjali Mehra have? | Upper Respiratory Infection (J06.9) |
| 3 | What is David Thompson's diabetes diagnosis code? | E11.9 — Type 2 Diabetes Mellitus |
| 4 | What specialty should I book for a kidney disease patient? | Nephrologist |
| 5 | What medication is Ramesh currently taking? | Telmisartan 40mg OD |

**Pass criteria:** ≥ 4/5 graded CORRECT by QAEvalChain

---

## Quick Test Checklist

Use this checklist when grading the submission:

- [ ] TC-01-A: Retrieve known patient history
- [ ] TC-01-C: Unknown patient returns error (no hallucination)
- [ ] TC-02-B: Returns correct ICD code from PDF
- [ ] TC-03-A: Appointment confirmed with reference number
- [ ] TC-03-E: Unavailable specialty handled gracefully
- [ ] TC-04-A: Returns meaningful medical search result
- [ ] TC-05-A: Record updated and visible on re-retrieval
- [ ] TC-06-A: Full problem statement scenario — 3 tools in sequence
- [ ] TC-07-A: Multi-turn memory — no need to repeat patient name
- [ ] TC-10: QAEvalChain accuracy ≥ 80%
