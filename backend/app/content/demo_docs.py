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
