"""Generate simulated coursework data. These are not verified TPC facts."""
import os
from pathlib import Path

RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "simulated_generated"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

documents = {
    "doc_01_tpc_computer_studies_bsis_bsais.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: COMPUTER STUDIES COMPLEX (CCIS)
===============================================================================
Location ID: TPC-BLDG-CSC
Building Name: TPC Computer Studies Building / CCIS Building
Operating Hours: Monday - Saturday: 7:00 AM - 8:00 PM
Campus Location: North Campus Area, Talibon Polytechnic College, San Isidro, Talibon, Bohol

PROGRAMS SERVED:
1. Bachelor of Science in Information Systems (BSIS)
2. Bachelor of Science in Accountancy Information System (BSAIS)

FLOOR DIRECTORY & PROGRAM OFFICES:
- Ground Floor (1st Floor):
  * BSIS Department Office (Room CSC-104): Office of the BSIS Department Chair & Program Coordinator.
  * BSIS ComLab 1 / BSIS Room 1 (Room CSC-101): Computer Laboratory 1 (BSIS Database, SQL & Programming Lab - 45 Workstations).
  * BSIS ComLab 2 / BSIS Room 2 (Room CSC-102): Computer Laboratory 2 (Enterprise Systems, Web & Accounting Software Lab - 45 Workstations).
  * BSIS Room 3 (Room CSC-103): BSIS Systems Analysis, Software Engineering & Lecture Seminar Room.
  * Office of the CCIS Dean (Room CSC-105): Executive Dean Suite for Computer Studies.
  * TPC IT Helpdesk (Room CSC-106): Campus Network & Computer Support Office.
  * Restrooms / Comfort Rooms (CR):
    - Male Comfort Room (Male CR): Ground Floor East Hallway next to BSIS ComLab 1 (CSC-101).
    - Female Comfort Room (Female CR): Ground Floor West Hallway next to IT Helpdesk (CSC-106).
    - PWD CR: Ground Floor main lobby.

- Second Floor (2nd Floor):
  * BSAIS Department Office (Room CSC-202): Office of the BSAIS Program Coordinator.
  * BSIS Room 4 (Room CSC-201): Upper Level BSIS Systems Development & IT Lecture Classroom.
  * Accounting Information Systems Lab (Room CSC-203): BSAIS Audit & Accounting Software Lab.
  * Rooms CSC-204 to CSC-206: CCIS Lecture Classrooms.
  * Restrooms / Comfort Rooms (CR):
    - Male Comfort Room (Male CR): 2nd Floor East Corridor.
    - Female Comfort Room (Female CR): 2nd Floor West Corridor.

NAVIGATION DIRECTIONS:
From TPC Main Gate 1 at San Isidro, Talibon, Bohol, walk North along the main entrance walkway past the Library. The Computer Studies Building is located on the North side of the campus quadrangle.
""",

    "doc_02_tpc_main_academic_polsci_english_beced.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: MAIN ACADEMIC BUILDING (MAB)
===============================================================================
Location ID: TPC-BLDG-MAB
Building Name: TPC Main Academic Building
Operating Hours: Monday - Saturday: 7:00 AM - 7:30 PM
Campus Location: Central Campus Quadrangle, Talibon Polytechnic College, San Isidro, Talibon, Bohol

PROGRAMS SERVED:
1. Bachelor of Arts in Political Science (BA PolSci / BAPS)
2. Bachelor of Arts in English Language (BA English)
3. Bachelor of Early Childhood Education (BECEd / Education)

FLOOR DIRECTORY:
- Ground Floor (1st Floor):
  * BA Political Science Department Office (Room MAB-101): Program Chair for Political Science.
  * BA English Language Department Office (Room MAB-102): Program Chair for English Language Studies.
  * BECEd Department Office (Room MAB-103): Early Childhood Education Program Head.
  * College of Arts, Sciences & Education Dean's Office (Room MAB-104).
  * Rooms MAB-105 to MAB-108: Multi-purpose lecture rooms.
  * Restrooms (CR): Ground Floor Central Lobby (Male and Female CRs).

- Second Floor (2nd Floor):
  * Rooms MAB-201 to MAB-206: Political Science and English Seminar Classrooms.
  * Early Childhood Education Activity & Simulation Room (Room MAB-207).
  * Faculty Consultation Room (Room MAB-208).
  * Restrooms (CR): 2nd Floor West Wing (Male and Female CRs).

NAVIGATION DIRECTIONS:
From Main Gate 1, walk straight past the security checkpoint along the central covered walkway for 70 meters. The Main Academic Building is directly in front of the flag ceremony plaza.
""",

    "doc_03_tpc_criminology_building.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CRIMINOLOGY BUILDING (CRIM)
===============================================================================
Location ID: TPC-BLDG-CRIM
Building Name: TPC College of Criminology Building
Operating Hours: Monday - Saturday: 6:30 AM - 8:00 PM
Campus Location: East Campus Sector, Talibon Polytechnic College, San Isidro, Talibon, Bohol

PROGRAMS SERVED:
1. Bachelor of Science in Criminology (BSCrim)

FACILITIES & ROOMS:
- Ground Floor:
  * BSCrim Department Office (Room CRM-102): Office of the Criminology Dean & Program Head.
  * Criminology Faculty Room (Room CRM-101).
  * Mock Courtroom & Legal Trial Simulation Hall (Room CRM-103).
  * Defensive Tactics & Martial Arts Dojo (Room CRM-104).
  * Restrooms (CR): Ground Floor East Wing (Male CR and Female CR).
- Second Floor:
  * Crime Scene Investigation (CSI) Simulation Room (Room CRM-201).
  * Forensic Photography & Fingerprint Examination Room (Room CRM-202).
  * Rooms CRM-203 to CRM-206: Criminology Theory & Law Lecture Classrooms.
  * Restrooms (CR): 2nd Floor East Corridor (Male and Female CRs).

NAVIGATION DIRECTIONS:
From Main Gate 1, enter and turn right along the East walkway. Proceed 150 meters past the Gymnasium; the Criminology Building is on the right side.
""",

    "doc_04_tpc_agriculture_building.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: AGRICULTURE & AGRI-TECH COMPLEX
===============================================================================
Location ID: TPC-BLDG-AGRI
Building Name: TPC Agriculture Building & Field Office
Operating Hours: Monday - Saturday: 7:00 AM - 6:00 PM
Campus Location: South-West Campus Area, Talibon Polytechnic College, San Isidro, Talibon, Bohol

PROGRAMS SERVED:
1. Bachelor of Science in Agriculture (BSAg)

FACILITIES & ROOMS:
- Ground Floor:
  * BSAg Program Office (Room AGR-101): Office of the Agriculture Department Chair.
  * Soil Science & Plant Pathology Laboratory (Room AGR-102).
  * Post-Harvest Processing & Agricultural Storage (Room AGR-103).
  * Agriculture Faculty & Extension Specialists Office (Room AGR-104).
  * Restrooms (CR): Ground Floor South Hall (Male and Female CRs).
- Adjacent Outdoor Facilities:
  * TPC Crop Demo Plots and Vegetable Nurseries.
  * Shade House, Hydroponics Unit & Vermicomposting Shed.

NAVIGATION DIRECTIONS:
From Main Gate 1, head left past the Administration Building and follow the perimeter road toward the South-West farm sector (approximately 180 meters).
""",

    "doc_05_tpc_administration_building.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: ADMINISTRATION BUILDING
===============================================================================
Location ID: TPC-BLDG-ADM
Building Name: TPC Administration Building (Executive Offices)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: Front Campus Plaza, Talibon Polytechnic College, San Isidro, Talibon, Bohol

EXECUTIVE OFFICES & SERVICES:
- Ground Floor:
  * Office of the College Registrar (Room ADM-101): Transcripts, enrollment, student records.
  * Finance & Cashier Office (Room ADM-102): Tuition payment, fee assessment, permits.
  * Accounting & Budget Office (Room ADM-103).
  * Human Resource Management Office (HRMO) (Room ADM-104).
  * Restrooms (CR): Ground Floor Lobby (Male, Female, PWD).
- Second Floor:
  * Office of the College President (Room ADM-201): Executive Suite.
  * Vice President for Academic Affairs (VPAA) (Room ADM-202).
  * Board of Trustees Conference Room (Room ADM-203).
  * Quality Assurance & Accreditation Office (Room ADM-204).

NAVIGATION DIRECTIONS:
From Main Gate 1, the Administration Building is situated immediately to the left, 40 meters from the security checkpoint.
""",

    "doc_06_tpc_gymnasium_cultural_center.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: GYMNASIUM & CULTURAL CENTER
===============================================================================
Location ID: TPC-BLDG-GYM
Building Name: TPC Gymnasium and Cultural Activity Center
Operating Hours: Monday - Saturday: 7:00 AM - 8:30 PM
Campus Location: East Sports Zone, Talibon Polytechnic College, San Isidro, Talibon, Bohol

FACILITIES:
- Main Court: Full-sized wooden basketball court, volleyball court, badminton courts.
- Grandstand & Bleachers: 1,500 seating capacity for campus assemblies and sports fests.
- Stage & Cultural Performing Arts Backstage.
- Athletic Director & Sports Varsity Office (Room GYM-01).
- Physical Education (PE) Instructors Lounge (Room GYM-02).
- Shower & Locker Rooms: Male Locker Room (East), Female Locker Room (West).

NAVIGATION DIRECTIONS:
From Main Gate 1, proceed 160 meters East past the Main Academic Building. The Gymnasium is easily identified by its arched metal roof.
""",

    "doc_07_tpc_canteen_dining_hall.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CAMPUS CANTEEN & FOOD COURT
===============================================================================
Location ID: TPC-BLDG-CAN
Building Name: TPC Student Canteen and Dining Hall
Operating Hours: Monday - Saturday: 6:30 AM - 6:30 PM
Campus Location: Central Grounds next to Library, Talibon Polytechnic College, San Isidro, Talibon, Bohol

FACILITIES & FOOD STALLS:
- Main Dining Hall: Clean bench tables seating up to 250 students.
- Food Stations:
  * Station 1: Affordable hot meals (Value meals, rice, vegetables, fish, chicken).
  * Station 2: Snacks, sandwiches, native Bohol delicacies, bakery pastries.
  * Station 3: Fresh fruit shakes, refreshments, coffee, bottled drinking water.
- Handwashing sinks and water refilling stations.
- Restrooms (CR): Single-occupancy restrooms behind food stall area.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk straight for 85 meters down the central walkway; the Canteen is located between the Library and the Main Academic Building.
""",

    "doc_08_tpc_library_learning_center.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: COLLEGE LIBRARY & LEARNING RESOURCE
===============================================================================
Location ID: TPC-BLDG-LIB
Building Name: TPC College Library and Learning Resource Center
Operating Hours: Monday - Friday: 7:30 AM - 6:30 PM; Saturday: 8:00 AM - 4:00 PM
Campus Location: North-West Plaza, Talibon Polytechnic College, San Isidro, Talibon, Bohol

SECTIONS & FACILITIES:
- Ground Floor:
  * Circulation & Information Desk (Borrowing, returns, library cards).
  * General Reference & Periodicals Section (Newspapers, journals, magazines).
  * Graduate Theses, Feasibility Studies & BSIS Capstone Repository.
  * Head Librarian Office.
- Second Floor:
  * Quiet Study Carrels & Reading Hall (Capacity: 180 seats).
  * E-Library & Digital Research Lab (25 internet-connected research terminals).
  * Bohol Local History & Filipiniana Book Collection.

NAVIGATION DIRECTIONS:
From Main Gate 1, proceed 95 meters along the main path. The Library is the modern building on the left of the main quadrangle.
""",

    "doc_09_tpc_student_affairs_services.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: STUDENT AFFAIRS & SERVICES (SASO)
===============================================================================
Location ID: TPC-BLDG-SASO
Building Name: Office of Student Affairs and Services (SASO)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: Student Center Ground Floor, San Isidro, Talibon, Bohol

SERVICES & FUNCTIONS:
- SASO Director Suite (Room SAS-101): Student welfare, leadership programs, institutional recognition.
- Student Organizations Accreditation Desk (Room SAS-102): Campus clubs, academic societies.
- Student Discipline & Grievance Committee (Room SAS-103): Mediation, student handbook orientation.
- Campus Publication Office (Room SAS-104): The official TPC student newsletter and editorial staff.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 60 meters towards the Student Center building adjacent to the College Library.
""",

    "doc_10_tpc_medical_dental_clinic.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: HEALTH & WELLNESS CLINIC
===============================================================================
Location ID: TPC-BLDG-MED
Building Name: TPC Health, Medical & Dental Clinic
Operating Hours: Monday - Friday: 7:30 AM - 5:30 PM (Emergency nurse on duty during Saturdays)
Campus Location: Ground Floor Admin Annex, San Isidro, Talibon, Bohol

SERVICES & AMENITIES:
- Nurse Triage & Patient Assessment Desk (Room CLN-101).
- College Physician Consultation Office (Room CLN-102): Free doctor checkup for enrolled students.
- Dental Examination Unit (Room CLN-103): Routine oral hygiene checks.
- 4-Bed Recovery & Observation Ward (with oxygen support and basic emergency kits).
- Free medicines for minor ailments (headache, fever, stomachache, rehydration salts).

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 50 meters left past the Cashier's lobby. The Clinic is clearly marked with a green medical cross.
""",

    "doc_11_tpc_campus_security_lost_found.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CAMPUS SECURITY & LOST AND FOUND
===============================================================================
Location ID: TPC-BLDG-SEC
Building Name: Campus Security Headquarters & Lost and Found Unit
Operating Hours: 24 Hours / 7 Days a Week
Campus Location: Main Gate 1 Entrance Plaza, San Isidro, Talibon, Bohol

SERVICES & DESKS:
- Chief of Security Office (Room SEC-101): Campus emergency response, safety protocols.
- Visitor Pass & Vehicle Sticker Counter: Visitor logbook, temporary gate permits.
- Official Lost and Found Counter: Turn over lost student IDs, flash drives, wallets, books.
- CCTV Monitoring Command Station: 24/7 surveillance across campus hallways and perimeter.

NAVIGATION DIRECTIONS:
Located immediately at Main Gate 1, San Isidro, Talibon, Bohol, adjacent to the guard turnstiles.
""",

    "doc_12_tpc_guidance_counseling_center.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: GUIDANCE & COUNSELING CENTER
===============================================================================
Location ID: TPC-BLDG-GCC
Building Name: Guidance, Counseling and Psychological Testing Center
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: 2nd Floor Student Center Annex, San Isidro, Talibon, Bohol

SERVICES:
- Individual & Group Mental Health Counseling (Private & confidential session rooms).
- Psychological Appraisal & Personality Assessment for Freshmen and Graduating Students.
- Career Guidance & Job Placement Assistance.
- Exit Interview & Clearance Signing Desk.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 65 meters North-West towards the Student Center Annex, ascend to Floor 2.
""",

    "doc_13_tpc_supreme_student_government.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: SUPREME STUDENT GOVERNMENT (SSG)
===============================================================================
Location ID: TPC-BLDG-SSG
Building Name: Supreme Student Government (SSG) Headquarters
Operating Hours: Monday - Friday: 8:00 AM - 5:30 PM
Campus Location: Student Activity Pavilion, San Isidro, Talibon, Bohol

FACILITIES:
- SSG President & Executive Board Chamber (Room SSG-101).
- Legislative Assembly Meeting Room (Room SSG-102).
- Student Activity Logistics & Equipment Storage (P.A. systems, tents, event banners).
- Academic Council Coordination Desk.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 110 meters East toward the open pavilion near the Gymnasium.
""",

    "doc_14_tpc_nstp_cwts_rotc_headquarters.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: NSTP & ROTC COMMAND OFFICE
===============================================================================
Location ID: TPC-BLDG-NSTP
Building Name: National Service Training Program (NSTP) & ROTC Armory
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM; Sunday: 6:30 AM - 12:30 PM (Training Day)
Campus Location: South Grounds, Talibon Polytechnic College, San Isidro, Talibon, Bohol

SERVICES & FORMATIONS:
- Civic Welfare Training Service (CWTS) Program Coordinator Office (Room NSTP-101).
- Reserve Officers' Training Corps (ROTC) Commandant & Tactical Inspection Office (Room NSTP-102).
- ROTC Armory & Drill Equipment Depot (Room NSTP-103).
- Grandstand Parade Grounds & Drill Field.

NAVIGATION DIRECTIONS:
From Main Gate 1, follow the main perimeter path southward toward the athletic field (140 meters).
""",

    "doc_15_tpc_research_development_extension.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: RESEARCH & EXTENSION OFFICE (RDE)
===============================================================================
Location ID: TPC-BLDG-RDE
Building Name: Research, Development & Community Extension Office
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: 3rd Floor Administration Annex, San Isidro, Talibon, Bohol

PROGRAMS:
- Institutional Research Council & Journal Publication Desk.
- Community Outreach & Livelihood Extension Assistance Desk (Barangay San Isidro Projects).
- Ethics Review Board & Plagiarism Screening Unit (Turnitin checking).
- Faculty Research & Intellectual Property Assistance.

NAVIGATION DIRECTIONS:
From Main Gate 1, enter the Administration Building, proceed to the 3rd floor west wing.
""",

    "doc_16_tpc_audio_visual_conference_hall.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: AUDIO-VISUAL CENTER (AVR)
===============================================================================
Location ID: TPC-BLDG-AVR
Building Name: TPC Audio-Visual Conference Hall & Media Theater
Operating Hours: Monday - Saturday: 7:30 AM - 7:30 PM
Campus Location: 2nd Floor Main Academic Building, San Isidro, Talibon, Bohol

FACILITIES:
- Main AVR Theater: 200 comfortable tiered seats, dual 4K laser projection, surround audio.
- Audio-Visual Control Room & Media Technician Booth.
- Capstone Defense & Faculty Colloquium Conference Room (Room AVR-202).
- Air-conditioned seminar environment for campus symposia.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 70 meters straight into the Main Academic Building, ascend the central stairs to the second floor.
""",

    "doc_17_tpc_campus_chapel_ecumenical_center.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CAMPUS ECUMENICAL CHAPEL
===============================================================================
Location ID: TPC-BLDG-CHP
Building Name: TPC Ecumenical Chapel & Meditation Center
Operating Hours: Daily: 6:00 AM - 7:00 PM
Campus Location: Quiet Garden Grove, South-East Sector, San Isidro, Talibon, Bohol

FACILITIES:
- Main Sanctuary for Prayer, Reflection, and Christian Campus Fellowship.
- Meditation Altar & Quiet Corner.
- Campus Ministry Consultation Room (Room CHP-01).
- Holy Mass & Fellowship Schedules: First Friday Mass at 12:00 PM; Sunday interfaith services.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 130 meters toward the quiet tree garden behind the Criminology Building.
""",

    "doc_18_tpc_cashier_finance_services.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CASHIERING & FINANCE WINDOWS
===============================================================================
Location ID: TPC-BLDG-CSH
Building Name: Finance & Cashier Services Center
Operating Hours: Monday - Friday: 8:00 AM - 4:30 PM (No noon break during enrollment periods)
Campus Location: Ground Floor Administration Building East Wing, San Isidro, Talibon, Bohol

WINDOW COUNTERS & TRANSACTIONS:
- Window 1: Tuition Fee Installment Payments & Examination Permits.
- Window 2: Transcript of Records (TOR), Diploma, & Certification Fees.
- Window 3: Student ID Replacement, Insurance, & Library Card Fees.
- Window 4: Miscellaneous Student Assessments & UniFAST Tertiary Education Subsidy Processing.
- Accepted Payment Methods: Cash, Landbank, GCash, Maya.

NAVIGATION DIRECTIONS:
From Main Gate 1, enter the Administration Building. The Cashier windows are situated directly in the East lobby (40 meters from gate).
""",

    "doc_19_tpc_office_of_the_registrar.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: OFFICE OF THE COLLEGE REGISTRAR
===============================================================================
Location ID: TPC-BLDG-REG
Building Name: Office of the College Registrar (Admissions & Records)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: Ground Floor Administration Building West Wing, San Isidro, Talibon, Bohol

SERVICE COUNTERS:
- Window A: Freshmen & Transferee Enrollment Evaluation.
- Window B: Official Transcript of Records (TOR) & CAV Verification.
- Window C: Certificate of Enrollment, Good Moral Character, & Grades Verification.
- Window D: Adding/Dropping of Subjects, Course Shifting, & Graduation Clearance.
- Digital Archive & Student Permanent Records Vault.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 40 meters into the Administration Building; the Registrar is in the West wing across from the Cashier.
""",

    "doc_20_tpc_admissions_scholarships_office.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: ADMISSIONS & SCHOLARSHIPS UNIT
===============================================================================
Location ID: TPC-BLDG-SCH
Building Name: Scholarships, Grants & Admissions Information Office
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM
Campus Location: Ground Floor Student Center Room 102, San Isidro, Talibon, Bohol

SCHOLARSHIP DESKS:
- Desk 1: Free Higher Education Act (RA 10931 / UniFAST) Compliance & Validation.
- Desk 2: Tertiary Education Subsidy (TES) & Tulong Dunong Program (TDP).
- Desk 3: Talibon LGU Mayor's Scholarship & Bohol Provincial Academic Grant.
- Desk 4: TPC Academic Honors & Athletic Grant Desks.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 60 meters towards the Student Center building, room 102.
""",

    "doc_21_tpc_sports_complex_athletic_field.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: SPORTS COMPLEX & ATHLETIC OVAL
===============================================================================
Location ID: TPC-BLDG-SPT
Building Name: TPC Athletic Oval and Outdoor Sports Complex
Operating Hours: Daily: 6:00 AM - 7:00 PM
Campus Location: East Campus Sports Sector, San Isidro, Talibon, Bohol

FACILITIES:
- 400-Meter Athletic Running Track (Red cinder track).
- Central Grass Field for Soccer, Football, and Archery.
- Outdoor Sepak Takraw Court and Lawn Tennis Court.
- Covered Bleachers with 800 Spectator Capacity.
- Outdoor Physical Fitness Stations (Pull-up bars, parallel bars).

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 170 meters East past the Gymnasium toward the perimeter fields.
""",

    "doc_22_tpc_agriculture_experimental_farm.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: EXPERIMENTAL CROP & LIVESTOCK FARM
===============================================================================
Location ID: TPC-BLDG-FRM
Building Name: TPC Agricultural Research & Demonstration Farm
Operating Hours: Monday - Saturday: 6:30 AM - 5:30 PM
Campus Location: South-West Farm Boundary, San Isidro, Talibon, Bohol

AREAS:
- Plot 1: Lowland Rice & Corn Agro-Ecosystem Trials.
- Plot 2: High-Value Vegetable Greenhouses (Tomato, Bell Pepper, Eggplant).
- Plot 3: Bohol Indigenous Crops (Ubi Kinampay & Rootcrop Preservation Nursery).
- Plot 4: Small Ruminant & Poultry Demonstration Unit.
- Plot 5: Organic Fertilizer Composting Station.

NAVIGATION DIRECTIONS:
From Main Gate 1, take the South-West access road past the Agriculture Building (220 meters).
""",

    "doc_23_tpc_criminology_forensic_ballistics_lab.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: CRIMINOLOGY FORENSIC LABORATORIES
===============================================================================
Location ID: TPC-BLDG-FOR
Building Name: Criminology Forensic Science & Ballistics Research Center
Operating Hours: Monday - Friday: 7:30 AM - 6:30 PM
Campus Location: 2nd Floor Criminology Building, San Isidro, Talibon, Bohol

LABORATORY UNITS:
- Room CRM-202: Forensic Chemistry & Toxicology Unit (Drug screening reagents, microscopes).
- Room CRM-204: Dactyloscopy & Latent Print Development Lab (Fingerprint dust, magnifying comparators).
- Room CRM-205: Firearms Identification & Forensic Ballistics Comparison Room.
- Room CRM-206: Polygraphy / Lie Detection Examination Chamber.

NAVIGATION DIRECTIONS:
From Main Gate 1, proceed 150 meters East into the Criminology Building, take the east stairway to Floor 2.
""",

    "doc_24_tpc_bsis_software_innovation_hub.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: BSIS SOFTWARE INNOVATION HUB
===============================================================================
Location ID: TPC-BLDG-HUB
Building Name: TPC BSIS Software Innovation & Capstone Incubation Hub
Operating Hours: Monday - Saturday: 7:30 AM - 7:30 PM
Campus Location: Room CSC-204, Computer Studies Building, San Isidro, Talibon, Bohol

FACILITIES:
- 30 High-Performance Workstations for AI, Data Analytics, and Full-Stack Development.
- Prototyping Workshop with IoT sensors, Arduino kits, and Raspberry Pi boards.
- Agile Scrum Collaboration Tables & Whiteboards.
- Server Rack hosting local student web apps and ChromaDB vector instances.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 110 meters North to the Computer Studies Building, climb to the second floor, Room CSC-204.
""",

    "doc_25_tpc_student_handbook_dress_code.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: STUDENT HANDBOOK & DRESS CODE
===============================================================================
Location ID: TPC-POL-01
Building Name: TPC Campus Policies & Student Code of Conduct
Operating Hours: Enforced at all times during campus hours
Campus Location: Applicable across all buildings in San Isidro, Talibon, Bohol

KEY CAMPUS POLICIES:
1. ID Policy: The official TPC Student ID must be worn visibly around the neck at all times upon entering through Main Gate 1.
2. Uniform Schedule:
   - Monday, Tuesday, Thursday: Prescribed college uniform with black shoes.
   - Wednesday: College organization / Wash day shirts with casual slacks or jeans.
   - Friday: Department shirt / PE uniform for enrolled PE students.
3. Prohibited Attire: Sleeveless shirts, cropped tops, sandos, short shorts, torn jeans, and rubber slippers/flip-flops are strictly banned.
4. Clean As You Go (CLAYGO): Required across the Canteen, Library, and quadrangle benches.

NAVIGATION TO SASO / DISCIPLINE:
For uniform exemptions or replacement IDs, report to SASO on the Ground Floor Student Center (60 meters from Gate 1).
""",

    "doc_26_tpc_grading_examination_guidelines.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: ACADEMIC GRADING & EXAMS
===============================================================================
Location ID: TPC-POL-02
Building Name: TPC Academic Affairs & Examination Guidelines
Operating Hours: Enforced throughout Prelims, Midterms, Semi-Finals, and Finals
Campus Location: Applicable across all academic departments

GRADING SYSTEM:
- 1.00: 98 - 100% (Superior)
- 1.25: 95 - 97% (Outstanding)
- 1.50: 92 - 94% (Very Good)
- 1.75: 89 - 91% (Good)
- 2.00: 86 - 88% (Satisfactory)
- 2.25: 83 - 85% (Fair)
- 2.50: 80 - 82% (Average)
- 2.75: 77 - 79% (Below Average)
- 3.00: 75 - 76% (Passing Grade)
- 5.00: Below 75% (Failed)
- INC: Incomplete (Must be cleared within one academic semester)

EXAMINATION RULES:
- Examination permits stamped by the Cashier must be presented to proctors before sitting for major exams.
- Electronic devices (smartphones, smartwatches) must be stored inside bags during exams.
""",

    "doc_27_tpc_campus_wifi_lms_portal.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: WI-FI & IT PORTAL SERVICES
===============================================================================
Location ID: TPC-POL-03
Building Name: Campus IT Network & Student Portal Services
Operating Hours: Monday - Saturday: 7:00 AM - 8:00 PM
Campus Location: IT Helpdesk, Room CSC-106, Computer Studies Building

IT ACCESS & SERVICES:
1. Campus Wi-Fi SSID: 'TPC-Student-WiFi' (Coverage: Library, CSC, MAB, Canteen).
2. Wi-Fi Access Credentials: Log in using your TPC Student ID Number and registered birthday (YYYYMMDD).
3. Student Portal URL: Check official grades, balance assessment, and enrolled schedule online.
4. Account Assistance: Password resets and account unlocking are done at the IT Helpdesk, Room CSC-106.

NAVIGATION DIRECTIONS:
From Main Gate 1, walk 110 meters North into the Computer Studies Building, Ground Floor Room CSC-106.
""",

    "doc_28_tpc_disaster_risk_evacuation_centers.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: DISASTER SAFETY & EVACUATION ZONES
===============================================================================
Location ID: TPC-POL-04
Building Name: Campus Disaster Risk Reduction & Evacuation Protocol
Operating Hours: 24/7 Campus Emergency Readiness
Campus Location: San Isidro, Talibon, Bohol

EMERGENCY PROTOCOLS:
1. Primary Evacuation Zone 1: Central Flagpole Plaza (Open space between MAB and Library).
2. Primary Evacuation Zone 2: Open Athletic Oval & Football Field (East Sector).
3. Earthquake Procedure: 'Duck, Cover, and Hold' until shaking ceases; evacuate calmly using exterior staircases. Do not use elevators.
4. Fire Alarm Pull Stations & Extinguishers: Located every 20 meters along building hallways.
5. Campus Emergency Hotline: Contact Campus Security Guard House at Main Gate 1.
""",

    "doc_29_tpc_motorpool_facilities_management.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: MOTORPOOL & MAINTENANCE COMPLEX
===============================================================================
Location ID: TPC-BLDG-MTR
Building Name: TPC Motorpool & Physical Facilities Management Office (PFMO)
Operating Hours: Monday - Friday: 7:30 AM - 5:00 PM
Campus Location: South-East Perimeter, San Isidro, Talibon, Bohol

SERVICES & FUNCTIONS:
- Official College Bus, Van, and Utility Vehicle Maintenance & Dispatch.
- Campus Electrical, Plumbing, Carpentry, and Air-conditioning Repairs.
- Classroom Sound System and Special Event Setup Requests.
- General Physical Facilities Maintenance and Groundskeeper Headquarters.

NAVIGATION DIRECTIONS:
From Main Gate 1, proceed along the eastern perimeter road behind the Gymnasium for 190 meters.
""",

    "doc_30_tpc_official_faq.txt": """===============================================================================
TALIBON POLYTECHNIC COLLEGE (TPC) DIRECTORY: FREQUENTLY ASKED QUESTIONS (FAQ)
===============================================================================
Location ID: TPC-DOC-FAQ
Building Name: TPC Campus Information & Frequently Asked Questions (FAQ)
Operating Hours: Monday - Saturday: 7:00 AM - 8:00 PM
Campus Location: Talibon Polytechnic College, San Isidro, Talibon, Bohol

FREQUENTLY ASKED CAMPUS QUESTIONS:

Q1: What academic degree programs are offered at Talibon Polytechnic College (TPC)?
A: TPC offers the following undergraduate programs:
   1. Bachelor of Science in Information Systems (BSIS)
   2. Bachelor of Science in Accountancy Information System (BSAIS)
   3. Bachelor of Science in Criminology (BSCrim)
   4. Bachelor of Science in Agriculture (BSAg)
   5. Bachelor of Arts in Political Science (BA PolSci / BAPS)
   6. Bachelor of Arts in English Language (BA English)
   7. Bachelor of Early Childhood Education (BECEd)

Q2: Where is the BSIS Department Chair Office located?
A: The BSIS Department Office is located in Room CSC-104 on the Ground Floor of the TPC Computer Studies Building (CCIS Complex).

Q3: Where can I pay my tuition fees or purchase an exam permit?
A: Payments and exam permits are handled at the Finance & Cashier Office in the Administration Building East Wing (Windows 1-4).

Q4: What are the library operating hours?
A: The College Library is open Monday to Friday from 7:30 AM to 6:30 PM, and Saturday from 8:00 AM to 4:00 PM.

Q5: What should I do if I lose my student ID or personal items?
A: Report immediately to the Campus Security Headquarters & Lost and Found Unit at Main Gate 1. Replacement ID requests are processed at SASO (Student Center).

Q6: Where can I obtain my Transcript of Records (TOR) or Certificate of Grades?
A: Request documents at the Office of the College Registrar, Ground Floor Administration Building West Wing.

Q7: What is the official campus dress code?
A: Students must wear their official TPC Student ID visibly at all times. The college uniform is worn on Mon/Tue/Thu, department shirt on Wed, and casual or PE clothes on Fri. Slippers and short shorts are prohibited.
"""
}

for filename, content in documents.items():
    filepath = os.path.join(RAW_DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Generated {len(documents)} SIMULATED documents in {RAW_DATA_DIR}; staff review is required before use.")
