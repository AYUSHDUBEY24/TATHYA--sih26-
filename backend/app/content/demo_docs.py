"""
Fictional demo document content (Phase 10A).

All text is entirely synthetic. Designed to support full-text search,
RAG retrieval, and AI demonstration with internally consistent fictional facts.
"""

FRAUD_FIR = """FIRST INFORMATION REPORT
Police Station: Cyber Crime Division, Bengaluru Urban
FIR Number: 26/2026
Date of Registration: 2026-01-15
Under Sections: 420 IPC, 66D IT Act 2000

COMPLAINANT:
Mr. Arjun Mehta, age 42, resident of Koramangala 4th Block, Bengaluru.

INCIDENT SUMMARY:
On 2026-01-12 at approximately 14:30 hours, the complainant received a
misspelled email appearing to originate from National Payment Services.
The email instructed him to click a link and enter banking credentials.

Within forty-five minutes, unauthorised transactions totalling
Rs. 4,85,000 were debited from his account through sixteen rapid
transfers to four mule accounts across three banks.

INVESTIGATING OFFICER:
Inspector Kavita Reddy, Cyber Crime Division.
"""

FRAUD_WITNESS_STATEMENT_01 = """WITNESS STATEMENT
Case Reference: CASE-2026-001
Witness: Ms. Priya Sharma, age 38, Senior Manager, National Payment Services
Date of Statement: 2026-01-18

STATEMENT:
In January 2026, our threat intelligence team detected a credential-harvesting
operation targeting our customers. The attacker registered the lookalike domain
npscorp-verify.com on 2026-01-10. The domain resolved to a virtual private
server hosted in Eastern Europe, IP address 185.220.101.34.

The phishing page used the Evilginx2 framework, which acts as a reverse proxy,
forwarding requests to our genuine portal while capturing credentials and session
cookies in real time.

Between 2026-01-12 and 2026-01-14, our systems detected login attempts using
stolen session tokens from approximately 47 unique customer accounts.
"""

FRAUD_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-001 - Cyber Fraud / Phishing
Prepared by: Inspector Kavita Reddy
Date: 2026-02-20

EVIDENCE COLLECTED:
a) Email headers geolocated to bulletproof hosting, IP 185.220.101.0/24.
b) Phishing domain npscorp-verify.com registered 2026-01-10.
c) Bank transaction records showing transfers to mule accounts at
   Laxmi Cooperative Bank, Metropolitan Credit Union, and Janata Sahakari Bank.
d) Mule account KYC documents - all four accounts opened using forged identities.
e) CCTV footage from ATM locations showing cash withdrawals by masked individuals.
f) Mobile phone records linked to mule account holders.

DIGITAL FORENSICS:
Seized laptop contained Evilginx2 configuration files, a spreadsheet with
23 harvested account credentials, cryptocurrency wallet addresses on the
Ethereum blockchain, and chat logs with co-conspirators discussing fund laundering.

FINDINGS:
Organised cyber fraud ring operating from Eastern India with overseas connections.
Modus operandi: phishing, mule accounts, cryptocurrency conversion.
Total identified victims: 47. Estimated total fraud: approximately Rs. 38 lakh.
"""

FRAUD_FORENSIC_REPORT = """DIGITAL FORENSICS LABORATORY REPORT
Lab Reference: FSL/DIG/2026/0342
Case Reference: CASE-2026-001
Examiner: Dr. Suresh Kumar, Senior Digital Forensics Analyst
Date: 2026-02-15

ITEMS EXAMINED:
1. Lenovo ThinkPad laptop, serial PF1X4N2, recovered from accused residence.
2. Samsung Galaxy M34 mobile phone, IMEI 356789012345678.

FINDINGS - LAPTOP:
Browser history shows 847 visits to phishing kit management URLs.
Evilginx2 framework found installed on the system.
harvests.db contained 23 unique username/password pairs and 47 session tokens.
Cryptocurrency wallet file found on desktop.

FINDINGS - MOBILE PHONE:
47 SMS messages to numbers linked to mule account holders.
WhatsApp chats discussing "transfers" and "cleaning".
Photographs of forged Aadhaar cards used for mule account opening.
"""

FRAUD_CHARGE_SHEET = """CHARGE SHEET
Court of the Judicial Magistrate First Class, Bengaluru
Case Number: CC 112/2026
Date: 2026-03-10

ACCUSED:
1. Rohit Verma, age 28, resident of MG Road, Patna.
2. Mohammad Irfan, age 31, resident of Kadipur, Gaya.
3. Vikram Jha, age 26, resident of Digha, Patna.

OFFENCES:
Sections 420, 467, 468, 471 IPC and Sections 66, 66D IT Act.

Total fraud amount: Rs. 38 lakh across 47 victims.
The accused were arrested on 2026-03-01.
"""
PROPERTY_FIR = """FIRST INFORMATION REPORT
Police Station: Civil Lines, Pune District
FIR Number: 142/2026
Date of Registration: 2026-02-03
Under Sections: 464, 465, 468, 471 IPC

COMPLAINANT:
Mrs. Sunita Deshmukh, age 58, resident of Sadashiv Peth, Pune.

INCIDENT SUMMARY:
The complainant alleges that her signature was forged on a registered Sale
Deed (Document No. 4521/2025) transferring her ancestral property at Survey
No. 84/2, Erandwane, Pune, to Green Valley Constructions Pvt. Ltd.

The property is a 2,400 sq ft residential plot valued at Rs. 2.8 crore.
The forged sale deed shows a sale consideration of only Rs. 35 lakh.

INVESTIGATING OFFICER:
Inspector Rajesh Patil, Economic Offences Wing.
"""

PROPERTY_WITNESS_STATEMENT_01 = """WITNESS STATEMENT
Case Reference: CASE-2026-002
Witness: Mr. Anand Kulkarni, age 65, retired Sub-Registrar
Date of Statement: 2026-02-10

STATEMENT:
I was the registering officer for Document No. 4521/2025.
The Aadhaar biometric authentication failed on the first attempt and
succeeded on the second attempt 23 minutes later. The facial photograph
captured does not match the complainant but shows a younger female,
believed to be a proxy attestor.

The stamp duty of Rs. 1,75,000 was paid through a demand draft
issued by Bank of Maharashtra, Erandwane branch.
"""

PROPERTY_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-002 - Property Forgery
Prepared by: Inspector Rajesh Patil
Date: 2026-03-25

KEY FINDINGS:
- The sale deed was registered using a proxy attestor who impersonated
  the complainant through Aadhaar biometric authentication.
- The attesting witnesses are employees of Green Valley Constructions.
- The stamp duty was paid by Green Valley Constructions.
- The property was targeted due to its high market value of Rs. 2.8 crore.
"""

NARCOTICS_FIR = """FIRST INFORMATION REPORT
Police Station: Narcotics Control Bureau, Zonal Unit Hyderabad
FIR Number: NCB/HYD/08/2026
Date of Registration: 2026-01-28
Under Sections: NDPS Act - 21(c), 25A, 29

SEIZURE:
On 2026-01-28 at 03:30 hours, a Tata 407 mini-truck was intercepted
at the NH-16 checkpoint, 15 km before Hyderabad city limits.

Recovered from the vehicles false bottom compartment:
- 12.5 kilograms of heroin in 25 sealed polythene packets.
- 2 mobile phones and Rs. 2,35,000 cash.
- A GPS device showing travel from Vizag port.

INVESTIGATING OFFICER:
Deputy Superintendent Raghunath Rao, NCB Hyderabad.
"""

NARCOTICS_WITNESS_STATEMENT_01 = """WITNESS STATEMENT
Case Reference: CASE-2026-003
Witness: Mr. Karunakar Reddy, age 44, petrol bunk owner
Date of Statement: 2026-01-30

STATEMENT:
I observed the Tata 407 mini-truck approaching at high speed.
The driver appeared nervous and was sweating despite the cool weather.
I signed as an independent pancha witness. The contraband weighed 12.5 kg.
The cash seized totalled Rs. 2,35,000 in Rs. 500 and Rs. 200 notes.
"""
NARCOTICS_FORENSIC_REPORT = """FORENSIC SCIENCE LABORATORY REPORT
Lab Reference: FSL/NAR/2026/0118
Case Reference: CASE-2026-003
Examiner: Dr. Meena Iyer, Chemical Analyst
Date: 2026-02-05

TESTS PERFORMED:
1. Marquis reagent test: Positive for opiate class.
2. TLC: Rf value 0.52, consistent with diacetylmorphine (heroin).
3. GC-MS: Confirmed diacetylmorphine (heroin).
4. Purity: 68% to 74%, indicating high-grade heroin.

Total net weight: 12,300 grams (commercial quantity threshold: 250 grams).
"""

NARCOTICS_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-003 - Narcotics Trafficking
Prepared by: DSP Raghunath Rao
Date: 2026-03-15

NETWORK IDENTIFIED:
- Overseas supplier based in Iran, receives payment in cryptocurrency.
- Port facilitator: Mr. Suresh Naik, Visakhapatnam.
- Transporters: Mr. Venkatesh Dharala (arrested) and 2 associates.
- Distribution: 3 retail-level dealers in Hyderabad identified.
"""

EMBEZZLEMENT_FIR = """FIRST INFORMATION REPORT
Police Station: Economic Offences Wing, Delhi
FIR Number: EOW/206/2026
Date of Registration: 2026-03-01
Under Sections: 406, 409, 120B IPC

COMPLAINANT:
Chairman, Delhi State Cooperative Bank.

INCIDENT SUMMARY:
Systematic embezzlement of Rs. 12.7 crore over four years (2022-2026).
Perpetrated by Branch Manager Mr. Ashok Pujari and CA Mr. Faisal Ahmed.
Modus operandi: fictitious loan accounts, forged KYC documents,
routing through 12 shell companies, cash withdrawals.

INVESTIGATING OFFICER:
Inspector Deepak Chauhan, EOW Delhi.
"""

EMBEZZLEMENT_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-004 - Financial Embezzlement (CLOSED)
Prepared by: Inspector Deepak Chauhan
Date: 2026-06-15

STATUS: CLOSED - Convicted

OUTCOME:
Both accused arrested on 2026-03-20. Convicted on 2026-06-10.
Sentence: 7 years rigorous imprisonment and Rs. 50 lakh fine each.
Assets worth Rs. 7.55 crore attached under Section 102 IPC.
"""

ASSAULT_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-005 - Assault (COURT STAGE)
Prepared by: Inspector Mohit Singh
Date: 2026-04-01

BACKGROUND:
On 2026-03-15, Mr. Rahul Khanna was assaulted outside a restaurant
in Hauz Khas Village, Delhi by a group of four individuals.

INJURIES:
Fracture of left zygomatic bone, laceration on forehead (8 stitches),
contusion on right forearm. Grievous hurt under Section 320 IPC.

STATUS:
All four accused arrested. Chargesheet filed. Case at COURT STAGE.
"""

MISSING_FIR = """FIRST INFORMATION REPORT - MISSING PERSON
Police Station: Sultanpur Lodhi, Kapurthala District
FIR Number: 09/2026
Date of Registration: 2026-04-05
Under Sections: 363 IPC

MISSING PERSON:
Ms. Harleen Kaur, age 19, B.Com student at Khalsa College, Kapurthala.
Last seen on 2026-04-04 at 17:00 hours leaving college.
Mobile phone switched off from 17:23 hours.

DESCRIPTION:
Height 5 feet 4 inches, fair complexion, mole on left cheek, wears spectacles.
Last seen wearing blue salwar kameez, carrying brown handbag.

INVESTIGATING OFFICER:
Sub-Inspector Balwinder Singh, Sultanpur Lodhi.
"""

MISSING_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-006 - Missing Person (UNDER INVESTIGATION)
Prepared by: SI Balwinder Singh
Date: 2026-04-12

FINDING:
Preliminary investigation indicates this is likely an elopement.
The missing person and Mr. Jaspreet Singh (classmate) have been in
regular contact for three months via social media.
CCTV shows the missing person entering a white Innova at Kapurthala bus stand.
No evidence of coercion or foul play.

STATUS: UNDER INVESTIGATION.
"""

ARMS_INVESTIGATION_REPORT = """INVESTIGATION REPORT
Case: CASE-2026-007 - Arms Trafficking (ARCHIVED)
Prepared by: Inspector Anil Dabke, ATS Mumbai
Date: 2026-05-01

STATUS: ARCHIVED - Convicted, sentence served

OPERATION:
On 2024-09-12, coordinated raids at three locations in Mumbai region.
Seized: 23 country-made pistols, 158 rounds of ammunition,
manufacturing lathe and tooling equipment.

5 persons arrested and convicted under the Arms Act.
"""

NARCOTICS_EVIDENCE_RECORD = """EVIDENCE RECORD
Case: CASE-2026-003 - Narcotics Trafficking (NCB Hyderabad)
Evidence ID: EV-2026-003-A
Seized on: 2026-02-20 at NH-16 toll checkpoint, Nellore district

SEIZED PROPERTY:
1. Package of 12 packets, white powder, gross weight 12.5 kg.
   Field test (Marquis reagent): presumptive positive for heroin/diacetylmorphine.
2. One Samsung Galaxy A54 mobile phone (IMEI 354918110233457) recovered
   from the driver, Mr. Imran Qureshi.
3. Cash of Rs. 3,40,000 in a black travel bag on the rear seat.

CHAIN OF CUSTODY:
2026-02-20: Seized by SI Lakshmi Narayana, handed to evidence custodian
            Constable M. Ravi, Malkhana NCB Hyderabad, shelf B-14.
2026-02-22: Samples 1 and 4 (total 50 g) drawn as per standing orders and
            forwarded to FSL Hyderabad under memo FSL/NARC/2026/447.
2026-02-25: Remaining bulk resealed and returned to Malkhana shelf B-14.
Integrity: seal number NC-88121, intact at every recorded transfer.

STATUS: Under examination. FSL report awaited.
"""

ASSAULT_COURT_FILING = """COURT FILING - CHARGESHEET COPY / COMMITTAL MEMO
Case: CASE-2026-005 - Assault, Hauz Khas Village
Court: Court of the Additional Sessions Judge, Saket Courts, New Delhi
CC Number: 112/2026
Filed on: 2026-04-18 by Adv. Meera Sharma, Additional Public Prosecutor

ACCUSED:
1. Mr. Vikram Sethi, age 26
2. Mr. Nilesh Bansal, age 24
3. Mr. Rohan Gupta, age 25
4. Mr. Tarun Oberoi, age 27

SECTIONS CHARGED: 326, 34 IPC (grievous hurt by dangerous means, common
intention). Section 326 invoked on the basis of the MLC and the radiology
report confirming fracture of the left zygomatic bone of the victim,
Mr. Rahul Khanna.

DOCUMENTS RELIED UPON:
1. FIR 45/2026, PS Hauz Khas, registered on 2026-03-15.
2. MLC of the victim from trauma centre, dated 2026-03-15 (8 stitches,
   left forearm contusion recorded).
3. CCTV footage from the restaurant entrance showing the assault at 22:41 hours.
4. Statements of two independent witnesses recorded under Section 161 CrPC.

PRAYER:
Accused are on bail. Evidence be summoned and the case be committed
for trial on the next date of hearing, 2026-05-20.
"""

# =====================================================================
# SHOWCASE CASE 1 - CASE-2026-0101 Operation Digital Shield (CYBER FRAUD)
# All names, banks, accounts and figures below are FICTIONAL demo data.
# =====================================================================

FRAUD_PHISHING_FIR = """FIR No. 0182/2026  (FICTIONAL DEMO RECORD - NOT A REAL FIR)
Police Station: Cyber Crime Cell - North District
Offence: Sections 66C and 66D, Information Technology Act, 2000 read with
Sections 318(4) and 316(2), Bharatiya Nyaya Sanhita, 2023.

Complainant: Mr. Devansh Pillai, age 41, resident of Ashok Vihar (fictional).
Incident date: 2026-07-02. FIR registered: 2026-07-04.
Operation code name: OPERATION DIGITAL SHIELD.

BRIEF FACTS:
1. On 2026-07-02 at about 11:20 hrs the complainant received an SMS claiming to
   be from "Meridian Trust Bank" (fictional) warning that his KYC would expire
   and asking him to update details on a look-alike website.
2. After entering net-banking credentials and one OTP, Rs. 2,40,000 was debited
   in three transactions within 9 minutes.
3. Customers of the same bank across North District reported identical losses.
   As on 2026-07-31, 214 complaints totalling Rs. 48,60,000 are on record.
4. Preliminary technical analysis shows the phishing page was hosted on a
   look-alike domain and funds were layered through multiple mule accounts.

PRAYER: Registration of FIR, preservation of digital evidence, and investigation
against unknown persons operating the phishing infrastructure.
"""

FRAUD_PHISHING_BANK_ANALYSIS = """BANK TRANSACTION ANALYSIS REPORT - OPERATION DIGITAL SHIELD
Case: FIR 0182/2026, CASE-2026-0101, Cyber Crime Cell - North District.
Prepared by: Financial Analysis Cell (fictional). Date: 2026-08-05.
CONFIDENTIAL - figures are fictional and used only for demonstration.

SCOPE: 214 victim complaints; 61 debit accounts; 9 beneficiary account clusters.

KEY FINDINGS:
1. All 214 victims debited funds within a 6-day window (2026-07-01 to
   2026-07-06), between 11:00 and 15:00 hrs, matching the phishing SMS pattern.
2. Funds moved in a three-hop pattern: victim account -> mule account (opened
   2026-05 onwards with low KYC history) -> aggregator account -> cash
   withdrawal or prepaid-card purchase.
3. Cluster "M-A1" (7 mule accounts) received Rs. 12,10,000 from 43 victims.
4. Cluster "M-A2" (11 mule accounts) received Rs. 17,35,000 from 68 victims.
5. Cluster "M-A3" (9 mule accounts, including the account that received the
   complainant's Rs. 2,40,000) received Rs. 19,15,000 from 103 victims.
6. Two aggregator accounts show ATM withdrawals in the jurisdiction of the
   Industrial Area Police Station within 40 minutes of credit.

CONCLUSION: A single organised crew operates the three clusters. Device and
email artefacts recovered from the suspects corroborate common control.
"""

FRAUD_PHISHING_EMAIL_EVIDENCE = """PHISHING EMAIL / SMS EVIDENCE REPORT
Case: CASE-2026-0101 (FIR 0182/2026). Compiled: 2026-08-08.
Classification: CONFIDENTIAL. All artefacts are synthetic demonstration data.

ARTEFACT INVENTORY (17 items preserved with hash values in the case file):
1. Phishing SMS template A - "Meridian Trust Bank: Your KYC expires today.
   Update now: m-eridiantrust-kyc[.]secure-login[.]top" - sent to 9,400 numbers
   via a bulk-SMS gateway account created on 2026-06-24.
2. Phishing SMS template B - refund variant - sent to 2,150 numbers on
   2026-07-05.
3. Fake KYC page (HTML mirror recovered) - collects username, password and OTP;
   posts them to a command server at 203.0.113.77 (documentation address,
   fictional) within 2 seconds of entry.
4. Bank-branded logo assets copied from a legitimate marketing email of
   2026-03-11.
5. Gateway logs show 214 successful OTP submissions correlating exactly with the
   214 victim debits.

NOTE: The archive copy is preserved as a read-only evidence item; working
copies were analysed in the cyber lab.
"""

FRAUD_PHISHING_DEVICE_EXAM = """DIGITAL DEVICE FORENSIC EXAMINATION REPORT
Case: CASE-2026-0101. Examined at: Cyber Forensics Lab (fictional).
Examiner: Dr. Suresh Kumar, Forensic Officer. Report date: 2026-08-19.
Exhibits: C-1 mobile phone (Android), C-2 laptop (Acer).

FINDINGS:
1. Exhibit C-1 (phone of accused Vikram Shetty, fictional): contains the
   bulk-SMS gateway dashboard bookmark, the phishing-page HTML source, and a
   note listing three mule-account numbers matching clusters M-A1 to M-A3.
2. Browser history on C-2 (laptop) shows 61 logins to the fake KYC mirror
   between 2026-07-01 and 2026-07-06, with 214 captured-credential downloads.
3. A draft SMS recovered from C-1 reads "job kaam ho gaya, paisa aaj raat tak
   withdraw" sent to the second accused on 2026-07-06 at 21:04 hrs.
4. Hash values of all extracted artefacts were recorded and anchored in the
   case integrity register before copying.

OPINION: Exhibits C-1 and C-2 were used to operate the phishing infrastructure
described in FIR 0182/2026.
"""

FRAUD_PHISHING_PRELIM_REPORT = """PRELIMINARY INVESTIGATION REPORT - OPERATION DIGITAL SHIELD
Case: CASE-2026-0101, FIR 0182/2026. By: Insp. Arjun Malhotra.
Date: 2026-08-25. Status: UNDER INVESTIGATION.

SUMMARY OF INVESTIGATION SO FAR:
1. Three accused arrested: Vikram Shetty (SMS gateway operator), Nilesh Bansal
   (mule-account handler) and Rohan Gupta (cash withdrawal). One aggregator,
   Tarun Oberoi, is absconding.
2. Total verified loss: Rs. 48,60,000 across 214 complaints; recovery of
   Rs. 6,80,000 made by freezing four mule accounts.
3. Technical evidence (phishing pages, gateway logs, device artefacts) has been
   preserved with hash anchors and is under forensic examination.
4. The look-alike domain registrar has been served a preservation notice dated
   2026-08-12.

NEXT STEPS:
- Complete examination of exhibits C-1 and C-2 and incorporate the FSL report.
- Trace the absconding aggregator through the mule-cluster KYC trail.
- Prepare the charge-sheet after the final bank reconciliation statement.

This report is a fictional demonstration document for the TATHYA platform.
"""

# =====================================================================
# SHOWCASE CASE 2 - CASE-2026-0102 Operation Paper Trail (DOCUMENT FORGERY)
# =====================================================================

FORGERY_FIR = """FIR No. 0143/2026  (FICTIONAL DEMO RECORD)
Police Station: Economic Offences Unit - Central District
Offence: Forgery of valuable security, forgery for purpose of cheating and
using forged document as genuine - Sections 336(3), 338 and 340(2), Bharatiya
Nyaya Sanhita, 2023.

Complainant: Mr. Harish Chandra Joshi, age 62, retired teacher (fictional).
Incident date range: 2026-02-10 to 2026-03-05. FIR registered: 2026-03-11.
Operation code name: OPERATION PAPER TRAIL.

BRIEF FACTS:
1. The complainant owns plot 47-B, Sunrise Enclave, Sector 21 (fictional
   township). On 2026-03-05 he received a possession notice from persons
   claiming to have purchased his plot through registered sale deed
   SG-214/2026 dated 2026-02-18.
2. The complainant never executed any sale deed and never visited the
   sub-registrar office on that date.
3. Scrutiny of the deed shows his signature on page 3 does not match known
   specimens, the identity proof annexed bears a mismatched photograph, and the
   stamp paper serial belongs to a batch reported stolen in 2026-01.
4. Registry records show the deed was presented through a proxy holder and
   registered using an Aadhaar-based biometric device whose session log shows
   three rejected fingerprint attempts before approval by override.

PRAYER: Registration of FIR, seizure of the forged deed, handwriting and
document examination, and action against the forgery network.
"""

FORGERY_SUSPECTED_DEED = """EXHIBIT RECORD - SUSPECTED FORGED SALE DEED SG-214/2026
Case: CASE-2026-0102 (FIR 0143/2026). Recorded: 2026-03-14.
Classification: EVIDENCE - handle under supervision of the IO.

DESCRIPTION OF EXHIBIT:
- Computerised sale deed, 6 pages + 2 schedule sheets, purportedly executed on
  2026-02-18 between vendor "Harish Chandra Joshi" (fabricated signature) and
  purchaser "Brightline Realtors LLP" (fictional entity).
- Stamp paper of Rs. 5,00,000 value, serial SP-2026-1187731 (from the stolen
  batch SP-2026-1187700 to 1187800, per treasury bulletin 04/2026 - fictional).
- Page 3 signature: slant inconsistent with vendor's 2019 bank specimen; ink
  strokes show pen-lift marks characteristic of tracing.
- Identity annexure: photocopy bearing the photograph of a different male
  person but identical demographic fields.
- Attesting witness "Sohan Lal" shares an address with a previously forged deed
  SG-88/2025 under examination in another file.

HANDLING NOTE: The exhibit is stored flat in an acid-free sleeve; the digital
scan attached to the case file is a working copy only.
"""

FORGERY_HANDWRITING_REPORT = """HANDWRITING AND SIGNATURE EXAMINATION REPORT
Case: CASE-2026-0102. Examined at: State Document Examination Division
(fictional). Examiner: Dr. Suresh Kumar, Forensic Officer. Dated: 2026-04-06.

QUESTIONED DOCUMENT: Signature of the vendor on page 3 of sale deed SG-214/2026.
STANDARDS: Ten admitted specimens of the vendor's signature from bank records
(2019-2025) and two affidavits.

FINDINGS:
1. Letter proportions, connecting strokes and terminal spurs of the questioned
   signature differ fundamentally from all admitted specimens.
2. The questioned signature shows uniform pen pressure and slow, deliberate
   formation consistent with free-hand tracing over a genuine model.
3. Microscopic examination reveals hesitation starts at the capital letter and
   pen-lift at the connecting loop - a natural signature does not show these.
4. The thumb impression on page 5 is a rubber-stamp reproduction, showing ink
   pooling at stroke junctions.

OPINION: The questioned signature and thumb impression are NOT genuine; they
are forged simulations and stamp reproductions respectively.
"""

FORGERY_AUTH_REPORT = """DOCUMENT AUTHENTICATION REPORT
Case: CASE-2026-0102. Prepared by: Forensic Records Unit (fictional).
Date: 2026-04-20. Exhibits: sale deed SG-214/2026 and annexures.

AUTHENTICATION FINDINGS:
1. Stamp paper serial SP-2026-1187731 belongs to the stolen batch reported by
   the district treasury on 2026-01-22; the licensed vendor's stock register
   shows this serial was never issued for sale.
2. The registration fee receipt quoted on the deed (receipt 88213 dated
   2026-02-18) does not exist in the sub-registrar receipt ledger; the nearest
   genuine receipt number is 88197.
3. The biometric device session log for the registration slot of 2026-02-18
   12:40-12:44 hrs shows three rejected fingerprint attempts followed by an
   operator override; the same device ID appears in the 2025 forgery file.
4. Paper watermarks on pages 4-6 differ from pages 1-3, indicating assembly
   from two separate sources.

CONCLUSION: Deed SG-214/2026 is a fabricated instrument assembled with a stolen
stamp paper and false registration particulars.
"""

FORGERY_FINDINGS = """INVESTIGATION FINDINGS - OPERATION PAPER TRAIL
Case: CASE-2026-0102, FIR 0143/2026. By: Insp. Meera Kapoor.
Date: 2026-05-08. Status: UNDER REVIEW.

FINDINGS:
1. The forgery was executed by a network of four persons: a document preparer,
   a proxy presenter, a biometric-device operator and a land broker. Two have
   been identified from CCTV at the sub-registrar office on 2026-02-18.
2. The same witness address and stamp-paper batch link this deed to SG-88/2025,
   indicating a continuing racket active since 2025.
3. Handwriting, authentication and treasury records independently confirm the
   deed is fabricated (see the FSL and authentication reports in this file).
4. Purchaser entity "Brightline Realtors LLP" was incorporated 11 days before
   the deed; its registered office is a shared co-working address used in three
   earlier suspect transactions.

RECOMMENDATION: Charge-sheet the identified persons under Sections 336(3),
338 and 340(2) BNS once the second transaction file is consolidated; preserve
all exhibits with integrity anchors for court production.

This file is a fictional demonstration record for the TATHYA platform.
"""

MISSING_PERSON_REPORT = """MISSING PERSON REPORT - OPERATION SAFE RETURN
Report No. MPR-0087/2026  (FICTIONAL DEMO RECORD)

Reporting Person: Mr. Devender Kohli (father), resident of 22 Riverside
Enclave, Model Town. Missing Person: Ms. Naina Kohli, age 19, B.Com
first-year student at Riverside Women's College.

LAST SEEN: 2026-02-08, approximately 18:40 hours, near the college
library gate. She was wearing a grey kurta and carrying a maroon
backpack. She left on her blue Scoot-E electric scooter (fictional
registration DL 8S FA 2091).

MEDICAL NOTE: Ms. Kohli is under treatment for anxiety; regular
medication is required, which raises urgency.

IO NOTE: Mobile phone last answered a call at 19:05 hours on
2026-02-08; thereafter the handset was either powered off or moved
outside network coverage. Parents confirm no family dispute.
"""

MISSING_INITIAL_INVESTIGATION = """INITIAL INVESTIGATION REPORT - OPERATION SAFE RETURN
Case: CASE-2026-0103  (FICTIONAL DEMO RECORD)
Prepared by: Insp. Kavya Nair, Riverside Police Station
Date: 2026-02-12

ENQUIRIES SO FAR:
a) College attendance records: Ms. Kohli attended all lectures on
   2026-02-08; faculty report nothing unusual in behaviour.
b) Friends interviewed (3): she had recently mentioned an online
   tuition group and a part-time content-writing assignment.
c) Scooter traced on RWW-Vahan portal: no towing or auction entry.
d) Bank account: no withdrawals after 2026-02-08; a UPI payment of
   Rs. 340 at a Model Town cafe at 17:55 hours was the last activity.
e) Hospital checks at Riverside Civil Hospital and St. Mary's
   Hospital: no admission matching the description.

PRELIMINARY DIRECTION: Obtain CCTV coverage along the route between
the college gate and Model Town roundabout for the 18:30-20:00 window.
"""

MISSING_CCTV_ANALYSIS = """CCTV ANALYSIS REPORT - OPERATION SAFE RETURN
Case: CASE-2026-0103  (FICTIONAL DEMO RECORD)
Analysed by: Digital Forensics Cell
Date: 2026-02-15

CAMERAS REVIEWED (fictional identifiers):
- CAM-RW-11 (college main gate): confirms Ms. Kohli exiting at
  18:41:22 hours on the blue scooter.
- CAM-MT-04 (Model Town roundabout): scooter passing at 18:53:07.
- CAM-MT-09 (market lane): last confirmed visual of the scooter at
  18:56:40, travelling north. No further camera captures it.

OBSERVATION: The market lane has a 400-metre blind stretch with no
coverage. Two pawn shops and a courier hub fall inside this stretch.

NO footage shows any second rider or forced stop. The trail ends at
the blind stretch, consistent with either a voluntary stop or an
abduction at that point.
"""

MISSING_MOBILE_LOCATION = """MOBILE LOCATION / CDR ANALYSIS - OPERATION SAFE RETURN
Case: CASE-2026-0103  (FICTIONAL DEMO RECORD)
Prepared by: Digital Forensics Cell
Date: 2026-02-16 (data via lawful interception under judicial order)

CDR SUMMARY (fictional cell identifiers):
- 19:05, 2026-02-08: last voice call answered, cell RW-NORTH-22,
  RSSI consistent with Model Town market lane.
- 19:06 to 19:58: handset remains registered on RW-NORTH-22 with
  deteriorating signal, then goes off-network.
- 2026-02-09, 03:12: single registration on cell RW-HIGHWAY-77 for
  41 seconds (brief service window), 62 km north of last location.
- No further activity to date.

INTERPRETATION: The brief 03:12 registration suggests the handset
travelled north on the national highway corridor. Toll-plaza data
request has been raised with the highway authority.
"""

MISSING_WITNESS_STATEMENTS_DOC = """WITNESS STATEMENTS (CONSOLIDATED) - OPERATION SAFE RETURN
Case: CASE-2026-0103  (FICTIONAL DEMO RECORD)
Recorded by: Insp. Kavya Nair
Dates: 2026-02-10 to 2026-02-14

STATEMENT 1 - Mr. Devender Kohli (father):
She left saying she would return by dinner. She had mentioned an
online tuition group that met in the evenings, but never missed
dinner without informing us.

STATEMENT 2 - Ms. Ritu Bansal (classmate):
Last week she said she had got a paid content-writing assignment
through a Telegram group and was to meet a coordinator once.

STATEMENT 3 - Mr. Salim Khan (tea stall, market lane):
On that evening around 7 o'clock I saw the blue scooter parked near
the courier hub for a long time. I did not see anyone sitting on it
or taking it away.

ASSESSMENT: Statements are mutually consistent. The courier hub angle
requires a premises search under warrant.
"""

VEHICLE_THEFT_FIR = """FIRST INFORMATION REPORT - OPERATION ROAD TRACE
FIR No. 0231/2026  (FICTIONAL DEMO RECORD)
Police Station: Industrial Area Police Station
Date of Registration: 2026-02-18
Under Sections: 303(2) BNS (theft), 336(3) BNS

COMPLAINANT: Ms. Farah Qureshi, logistics coordinator, Sunrise
Freight Solutions (fictional company).

INCIDENT: Between 2026-02-17 21:30 and 2026-02-18 06:15 hours, the
complainant's white Tata Ace goods carrier (fictional registration
DL 3C AC 4471, chassis fictional RC-VA-88231) was stolen from the
locked parking bay of the Industrial Area Phase-2 depot. The gate
guard reported the chain lock cut.

VEHICLE VALUE: approx. Rs. 7,80,000 including mounted cold-box.
"""

VEHICLE_REG_VERIFICATION = """VEHICLE REGISTRATION VERIFICATION - OPERATION ROAD TRACE
Case: CASE-2026-0104  (FICTIONAL DEMO RECORD)
Verified by: Insp. Rohit Verma via RWW-Vahan (fictional registry)
Date: 2026-02-19

REGISTRATION DETAILS (fictional):
- Registration: DL 3C AC 4471, white Tata Ace, 2023 model.
- Owner: Farah Qureshi, valid FC upto 2033.
- Insurance: Valid, National Mutual Assurance (fictional).
- NO hypothecation dispute; NOT reported sold.

Vahan alert feed: no re-registration or NOC entry for this number
after 2026-02-17. ANPR network request initiated for all district
cameras for the night of 2026-02-17/18.
"""

VEHICLE_CCTV_ROUTE = """CCTV ROUTE ANALYSIS - OPERATION ROAD TRACE
Case: CASE-2026-0104  (FICTIONAL DEMO RECORD)
Analysed by: District CCTV Cell
Date: 2026-02-21

ROUTE RECONSTRUCTION (fictional camera IDs):
- 22:14, CAM-IA-07: white Tata Ace exiting depot gate, no cabin load.
- 22:31, CAM-NH-24: same vehicle crossing the toll plaza with a
  different front number plate (plate swap suspected, rear plate
  matches DL 3C AC 4471).
- 23:05, CAM-EW-19: vehicle entering the East Warehouse cluster.
- No further ANPR hits after 23:20.

CONCLUSION: Number-plate substitution at or near the toll plaza
indicates an organised network using the East Warehouse cluster as a
transit point, consistent with three earlier unsolved depot thefts.
"""

VEHICLE_RECOVERY_MEMO = """RECOVERY MEMO - OPERATION ROAD TRACE
Case: CASE-2026-0104  (FICTIONAL DEMO RECORD)
Recovered by: Interception team led by Insp. Rohit Verma
Date/Time of recovery: 2026-02-24, 02:10 hours

On specific intelligence, the white Tata Ace (DL 3C AC 4471) was
recovered from Shed 14 of the East Warehouse cluster. The front
number plate read (fictional) UP 7L QT 9012; the original plate was
recovered from the cabin footwell. Cold-box intact; goods unopened.

Recovered vehicle handed to the Vehicle Examination Unit for
fingerprint and forensic sourcing. Two shed caretakers (fictional
names withheld, juveniles referred to board) detained for enquiry.
"""

VEHICLE_PROGRESS_REPORT = """INVESTIGATION PROGRESS REPORT - OPERATION ROAD TRACE
Case: CASE-2026-0104  (FICTIONAL DEMO RECORD)
Prepared by: Insp. Rohit Verma
Date: 2026-02-28

STATUS: Vehicle recovered; organised-theft module under development.

FINDINGS:
a) Warehouse Shed 14 rented (fictional lease) by a shell transport
   firm, M/s Kyari Roadlines, registered 2025-11.
b) Toll data ties the module to 4 theft-and-transit runs since
   December 2025.
c) Fingerprints from the swapped front plate matched a suspect with
   prior auto-theft history (fictional reference: history-sheet no.
   22/IAB).

NEXT: Verify ownership chain of M/s Kyari Roadlines; seek custody
extension for seized CCTV DVRs; coordinate with the insurance
assessor for loss quantification.
"""

EMBEZZLEMENT_COMPLAINT = """COMPLAINT REPORT - OPERATION LEDGER WATCH
Complaint No. EOW-CR-0092/2026  (FICTIONAL DEMO RECORD)
Police Station: Economic Offences Wing — East District
Date of Receipt: 2026-03-02

COMPLAINANT: Board of Trustees, Meridian Charitable Foundation
(fictional registered society), through its treasurer.

SUBJECT: Suspected embezzlement of approximately Rs. 1.15 crore by
a former accounts officer of the Foundation over 14 months.

BACKGROUND: The Foundation's internal audit (fictional engagement
2025-12) flagged 41 vendor payments to two suppliers that do not
appear to exist at the given addresses. Both supplier firms were
onboarded by the same accounts officer.

REQUEST: Register FIR, seize accounting systems, and preserve
bank records for the period 2025-01 to 2026-02.
"""

EMBEZZLEMENT_TRANSACTION_ANALYSIS = """FINANCIAL TRANSACTION ANALYSIS - OPERATION LEDGER WATCH
Case: CASE-2026-0105  (FICTIONAL DEMO RECORD)
Prepared by: Financial Analysis Unit, EOW
Date: 2026-03-08

METHOD: Forensic review of the Foundation's ledger (fictional
export LDG-2026-41) against bank statements for account
MF-TRUST-0091 (fictional).

KEY FINDINGS:
a) 41 payments totalling Rs. 1,14,85,600 to M/s Bharat Supply Link
   and M/s Varuni Traders (both fictional), invoiced as "civil works"
   and "stationery bulk supply".
b) Each payment just below the Foundation's Rs. 3,00,000
   dual-approval threshold — 38 of 41 split a single invoice into two
   parts within 48 hours.
c) Supplier firms share one registered email and one mobile number.
d) Funds exiting supplier accounts (fictional accounts) moved to 6
   personal accounts within 24 hours; from there to two prepaid-card
   wallets.

PATTERN: Classic threshold-splitting (structuring) with layered
disbursement through supplier shells.
"""

EMBEZZLEMENT_STATEMENT_REVIEW = """ACCOUNT STATEMENT REVIEW - OPERATION LEDGER WATCH
Case: CASE-2026-0105  (FICTIONAL DEMO RECORD)
Reviewed by: Financial Analysis Unit, EOW
Date: 2026-03-12

ACCOUNTS REVIEWED (fictional): MF-TRUST-0091 (Foundation), supplier
accounts BSL-7731 and VT-4409, and six personal accounts linked by
transfer flow.

OBSERVATIONS:
a) The Foundation account shows no genuine delivery-linked debits in
   the same period against the 41 flagged payments.
b) Supplier account BSL-7731: 100% of credits forwarded onwards
   within one business day — no operating expenses, no rent, no
   salaries. Inconsistent with a functioning supplier.
c) One personal account (fictional, linked to the former accounts
   officer's household) received Rs. 18,40,000 across five months
   and paid a travel agency and two jewellery merchants.
d) Round-trip test: no reversed/returned payments — consistent with
   completed siphoning rather than an accounting error.
"""

EMBEZZLEMENT_AUDIT_FINDINGS = """AUDIT FINDINGS SUMMARY - OPERATION LEDGER WATCH
Case: CASE-2026-0105  (FICTIONAL DEMO RECORD)
Source: Internal audit (fictional) conducted Dec 2025 by an external
CA firm for Meridian Charitable Foundation.

CONTROL FAILURES IDENTIFIED:
1. Vendor onboarding did not verify GSTIN or physical address.
2. Dual-approval threshold easily structured around; no cumulative
   monthly vendor limit.
3. Site-verification certificates were self-attested scans; two
   certificates reused the same serial number.
4. Bank reconciliation was signed off quarterly without statement
   comparison for 9 consecutive quarters.

QUANTIFICATION: Estimated exposure Rs. 1,14,85,600 across
2025-01 to 2026-02, matching the EOW transaction analysis.
"""

EMBEZZLEMENT_PRELIM_CHARGE = """PRELIMINARY CHARGE REPORT - OPERATION LEDGER WATCH
Case: CASE-2026-0105  (FICTIONAL DEMO RECORD)
Prepared by: Insp. Aditya Rao, EOW East District
Date: 2026-03-18

PRIMA FACIE OFFENCES: Criminal breach of trust by servant, cheating,
forgery of accounts (fictional statutory references under BNS 316/318
and records provisions).

ACCUSED (fictional): Former Accounts Officer (in service 2023-03 to
2026-01) and two unidentified associates operating the shell firms.

EVIDENCE STATUS: Ledger export, bank statements, onboarding files,
and the accounts laptop seized and hashed for integrity anchoring.

NEXT: Seek custodial interrogation; write to the wallet providers
under legal process; arrest memo preparation once the money trail
to the two wallets is certified by the analysis unit.
"""

CYBERSTALKING_COMPLAINT_FIR = """COMPLAINT AND FIR - OPERATION SILENT SHIELD
FIR No. 0312/2026  (FICTIONAL DEMO RECORD)
Police Station: Cyber Crime Unit — South District
Date of Registration: 2026-03-21
Under Sections: 78(2) BNS (stalking), 79 BNS, 66E/67 IT Act

COMPLAINANT: Ms. Tanvi Iyer, age 27, graphic designer, resident of
South District (fictional address).

INCIDENT: The complainant reports 7 months of unwanted contact:
a) 200+ anonymous social-media accounts repeatedly viewing and
   commenting on her professional portfolio.
b) Edited composite images of her circulated in two neighbourhood
   groups with insulting captions.
c) She believes the harasser knows her daily routine; two accounts
   posted locations minutes after she visited them.

IMPACT STATEMENT: Sleep disturbance; she has stopped attending
studio sessions alone.

EVIDENCE OFFERED: Screenshots archive, device for examination,
and social-media account handles (fictional).
"""

CYBERSTALKING_COMM_ANALYSIS = """DIGITAL COMMUNICATION ANALYSIS - OPERATION SILENT SHIELD
Case: CASE-2026-0106  (FICTIONAL DEMO RECORD)
Prepared by: Cyber Forensics Lab
Date: 2026-03-26

SCOPE: 3,412 screenshots (fictional archive SHA-covered) plus
voluntary production of the complainant's device data.

FINDINGS:
a) Of 214 suspicious accounts, 19 show identical posting-time
   fingerprints: activity only between 21:30-23:45 IST on weekdays.
b) All 19 accounts were created from the same device fingerprint
   (fictional browser canvas hash) on the same home ISP (fictional
   ISP: MetroNet Broadband).
c) Language analysis: repeated distinctive misspellings ("sturdi",
   "proffesnal") across accounts, matching the writing style of the
   complainant's former studio colleague (fictional person S.D.).
d) Two composite images carry EXIF remnants indicating an editing
   app installed on a Samsung device with a cracked screen protector
   (device profile consistent with the former colleague's device).
"""

CYBERSTALKING_SOCIAL_EVIDENCE = """SOCIAL MEDIA EVIDENCE REPORT - OPERATION SILENT SHIELD
Case: CASE-2026-0106  (FICTIONAL DEMO RECORD)
Compiled by: Insp. Ananya Sharma
Date: 2026-03-28

PLATFORM PRESERVATION: Preservation notices issued (fictional
ticket nos. SM-PRES-1183/1184) for 19 accounts; takedown request for
2 composite-image posts under IT Rules (fictional grievance IDs).

ACCOUNT CLUSTER MAP (fictional handles summarised): 19 accounts,
2 content-repost networks, 6 neighbourhood groups. Earliest account
creation: 2025-08-30 — six days after the complainant resigned from
the studio where the former colleague worked.

IMPORTANT: All handles, tickets, and grievance IDs are fictional.
"""

CYBERSTALKING_DEVICE_EXAM = """DEVICE FORENSIC EXAMINATION REPORT - OPERATION SILENT SHIELD
Case: CASE-2026-0106  (FICTIONAL DEMO RECORD)
Examined by: Cyber Forensics Lab (device produced under seizure memo)
Date: 2026-04-02

DEVICE: Samsung smartphone (fictional model), seized from the
suspect's residence with consent of a judicial magistrate order
(fictional order no. JM-SC-226/2026).

FINDINGS:
a) Editing app present with composite-image project files matching
   the two circulated images (hash-matched).
b) 14 of the 19 suspicious accounts logged in from this device.
c) Browsing history contains the complainant's public portfolio and
   the two neighbourhood groups on 41 dates.
d) Deleted chat fragment (recovered): "...us studio vale ko dekh
   lenge..." — corroborative of intent.

CHAIN: Device sealed, hashed at seizure and after imaging; both
hashes identical — no evidence of handling compromise.
"""

CYBERSTALKING_SUMMARY = """INVESTIGATION SUMMARY - OPERATION SILENT SHIELD
Case: CASE-2026-0106  (FICTIONAL DEMO RECORD)
Prepared by: Insp. Ananya Sharma
Date: 2026-04-06

CASE STATUS: Prima facie case established against the former studio
colleague (fictional person S.D.) under stalking and harassing-
communication provisions with IT Act provisions.

STRENGTH:
1. Device fingerprint + ISP + posting-time clustering ties 19
   accounts to one operator.
2. Hash-matched composite images found on the seized device.
3. Recovered chat fragment corroborates intent.

PENDING: Platform's preservation responses (2 outstanding);
advice from the legal officer on adding defamation counts; victim
counselling referral made to District Legal Services (fictional).

NOTE FOR DEMO: This file is synthetic; no real person, platform, or
grievance identifier exists.
"""

