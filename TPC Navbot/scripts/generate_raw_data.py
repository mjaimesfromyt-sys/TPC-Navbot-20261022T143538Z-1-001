import os

RAW_DATA_DIR = r"c:\Users\ranz\Desktop\TPC Navbot\data\raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

documents = {
    "doc_01_main_academic_building.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: MAIN ACADEMIC BUILDING (MAB)
===============================================================================
Location ID: BLDG-MAB-01
Building Name: Main Academic Building (MAB)
Operating Hours: Monday - Saturday: 7:00 AM - 8:30 PM

OVERVIEW:
The Main Academic Building is a 4-story facility located at the central plaza of TPC campus. It houses general education classrooms, lecture halls, and administrative offices.

FLOOR DIRECTORY:
- Floor 1 (Ground Floor):
  * Room MAB-101 to MAB-108: General Lecture Classrooms (Capacity: 45 students each).
  * Room MAB-109: Office of the Academic Dean (College of Arts & Sciences). Hours: 8:00 AM - 5:00 PM.
  * Room MAB-110: Audio-Visual Hall 1 (Capacity: 150 seats).
- Floor 2:
  * Room MAB-201 to MAB-212: Lecture Classrooms for Mathematics and Languages.
  * Room MAB-215: CAS Faculty Lounge and Consultation Room.
- Floor 3:
  * Room MAB-301 to MAB-310: General Education Classrooms.
  * Room MAB-312: Psychology & Social Sciences Testing Laboratory.
- Floor 4:
  * Room MAB-401 to MAB-405: Large Lecture Halls (MAB Hall A, Hall B).
  * Room MAB-406: University Speech & Communication Laboratory.

NAVIGATION DIRECTIONS:
Entering through the Main Gate, walk 100 meters straight down Central Avenue. The Main Academic Building is directly facing the Central Flagpole Plaza, situated between the Administration Building (East) and the Student Services Center (West).
""",

    "doc_02_engineering_technology_wing.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: ENGINEERING & TECHNOLOGY WING (ETW)
===============================================================================
Location ID: BLDG-ETW-02
Building Name: Engineering & Technology Wing (ETW)
Operating Hours: Monday - Saturday: 7:30 AM - 9:00 PM

OVERVIEW:
The Engineering & Technology Wing is a 3-story specialized building accommodating specialized engineering laboratories, drafting rooms, and technical workshops.

FLOOR DIRECTORY:
- Floor 1 (Ground Floor):
  * Room ETW-101: Heavy Machinery & Mechanical Engineering Workshop.
  * Room ETW-102: Civil Engineering Hydraulics & Materials Testing Lab.
  * Room ETW-103: Electrical Circuits & Power Systems Laboratory.
  * Room ETW-104: Engineering Dean's Office & Administrative Suite.
- Floor 2:
  * Room ETW-201: Electronics & Communications Engineering Lab.
  * Room ETW-202: Microprocessor & Embedded Systems Workshop.
  * Room ETW-203 to ETW-208: Engineering CAD & Computer Laboratories.
- Floor 3:
  * Room ETW-301: Industrial Engineering Ergonomics Lab.
  * Room ETW-302: Mechatronics & Automation Laboratory.
  * Room ETW-303 to ETW-306: Advanced Engineering Seminar Rooms.

NAVIGATION DIRECTIONS:
From the Main Academic Building, head East past the Science Complex. The Engineering & Technology Wing is recognizable by its blue steel structural frames and adjacent outdoor testing courtyard.
""",

    "doc_03_computer_studies_complex.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: COMPUTER STUDIES COMPLEX (CSC)
===============================================================================
Location ID: BLDG-CSC-03
Building Name: Computer Studies Complex (CSC) / IT Building
Operating Hours: Monday - Saturday: 7:00 AM - 9:30 PM

OVERVIEW:
The Computer Studies Complex (CSC) is a high-tech 4-story facility dedicated to Information Technology, Computer Science, and Information Systems programs.

FLOOR DIRECTORY:
- Floor 1 (Ground Floor):
  * Room CSC-101: Main Computer Laboratory 1 (General Programming).
  * Room CSC-102: Main Computer Laboratory 2 (Web Development & Multimedia).
  * Room CSC-105: College of Computer Studies (CCS) Dean's Office.
  * Room CSC-106: Server Room & Network Operations Center (Restricted Access).
- Floor 2:
  * Room CSC-201: Artificial Intelligence & Data Science Laboratory.
  * Room CSC-202: Cybersecurity & Networking Laboratory.
  * Room CSC-203: Mobile Application Development Studio.
  * Room CSC-204 to CSC-208: General IT Computer Classrooms.
- Floor 3:
  * Room CSC-301: Software Engineering Project Incubator.
  * Room CSC-302 to CSC-310: Computer Labs 3 through 10.
- Floor 4:
  * Room CSC-401: CCS Multimedia Auditorium & Gaming Tech Hub.
  * Room CSC-402: Robotics & IoT Prototyping Laboratory.

NAVIGATION DIRECTIONS:
Located on the North side of the campus quadrangle, right beside the Innovation & Incubation Hub. Accessible from Gate 2 via the Science & Tech Walkway.
""",

    "doc_04_administration_building.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: ADMINISTRATION BUILDING (ADM)
===============================================================================
Location ID: BLDG-ADM-04
Building Name: Administration Building (ADM)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM

OVERVIEW:
The Administration Building houses the executive leadership, central university administration, human resources, legal counsel, and institutional finance offices.

FLOOR DIRECTORY:
- Floor 1 (Ground Floor):
  * Room ADM-101: University Visitor Information & Protocol Desk.
  * Room ADM-102: Human Resource Management Office (HRMO).
  * Room ADM-103: Finance & Procurement Office.
- Floor 2:
  * Room ADM-201: Office of the University President.
  * Room ADM-202: Office of the Vice President for Academic Affairs (VPAA).
  * Room ADM-203: Office of the Vice President for Administration & Finance (VPAF).
  * Room ADM-204: Board of Trustees Executive Conference Room.

NAVIGATION DIRECTIONS:
Situated directly east of the Main Academic Building facing the main entrance circle. Look for the grand concrete pillars and flag plaza.
""",

    "doc_05_student_services_center.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: STUDENT SERVICES CENTER (SSC)
===============================================================================
Location ID: BLDG-SSC-05
Building Name: Student Services Center (SSC)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM; Saturday: 8:00 AM - 12:00 PM

OVERVIEW:
The Student Services Center is the primary hub for student administrative support, including academic records, enrollment, student welfare, and career counseling.

KEY OFFICES:
- Ground Floor:
  * Office of the Registrar (Window 1: Transcripts, Window 2: Diplomas, Window 3: Certifications, Window 4: Enrollment Verification).
  * Student Records Vault & Processing Unit.
- Second Floor:
  * Office of Student Affairs (OSA): Student organization accreditation, discipline, and campus event permits.
  * Guidance & Counseling Center (GCC): Individual counseling, testing, peer facilitators.
  * Scholarship & Financial Assistance Desk: CHED, private, and institutional grants.

NAVIGATION DIRECTIONS:
Located west of the Main Academic Building, across from the Student Center Plaza.
""",

    "doc_06_finance_accounting_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: FINANCE & CASHIER SERVICES (FIN)
===============================================================================
Location ID: OFFICE-FIN-06
Building: Student Services Center (Ground Floor East Wing)
Operating Hours: Monday - Friday: 8:00 AM - 4:00 PM (No noon break)

OVERVIEW:
The Finance & Cashier Services office handles student tuition payments, fee assessments, refunds, payment plan arrangements, and official receipt issuance.

SERVICE DESKS & COUNTERS:
- Counters 1 to 4: Tuition Fee Payments & Official Receipt Issuance.
- Counter 5: Assessment Validation & Payment Plan Adjustments.
- Counter 6: Refund Requests, Overpayment Claims, and Exam Permits.

PAYMENT POLICIES:
- Accepted payment methods: Cash, Manager's Check, GCash, Maya, Debit/Credit Card (Visa/Mastercard), Online Bank Transfer.
- Tuition Installment Deadlines: Prelim (Week 4), Midterm (Week 8), Semi-Final (Week 12), Final (Week 16).

NAVIGATION DIRECTIONS:
Enter the Student Services Center ground floor, turn right down the east hallway towards the glass enclosure marked "Cashier & Business Office".
""",

    "doc_07_university_library.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: LEARNING RESOURCE & UNIVERSITY LIBRARY (LIB)
===============================================================================
Location ID: BLDG-LIB-07
Building Name: University Library Building
Operating Hours: Monday - Friday: 7:30 AM - 7:00 PM; Saturday: 8:00 AM - 5:00 PM

OVERVIEW:
A 3-story modern facility providing print literature, digital research databases, group study rooms, and quiet reading areas.

FLOOR DIRECTORY:
- Floor 1:
  * Circulation Desk & Book Borrowing Counter.
  * General Periodicals, Newspapers & Magazines Section.
  * Discussion Zone & Coffee Kiosk.
- Floor 2:
  * Engineering, Technology & Computer Science Reference Section.
  * Digital Internet Research Laboratory (50 High-Speed PCs).
  * Discussion Rooms A through D (Reservable for up to 6 students).
- Floor 3:
  * Silent Study Zone (Strict Noise-Free Policy).
  * Thesis, Dissertation & Special Collections Section.
  * Filipiniana & Archives Collection.

BORROWING RULES:
- Students may borrow up to 5 circulation books for 7 days.
- Reserve books may be checked out for overnight use starting at 4:00 PM.

NAVIGATION DIRECTIONS:
Located directly opposite the Computer Studies Complex along Academic Drive.
""",

    "doc_08_health_wellness_clinic.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: HEALTH & WELLNESS CLINIC (CLN)
===============================================================================
Location ID: OFFICE-CLN-08
Building: Student Center Annex (Ground Floor)
Operating Hours: Monday - Saturday: 7:30 AM - 6:00 PM

OVERVIEW:
Provides free primary medical consultation, emergency first aid, physical examination validation, and dental health services to TPC students, faculty, and staff.

SERVICES & STAFF:
- Resident Physicians: Consultations available Monday to Friday 9:00 AM - 4:00 PM.
- Registered Nurses: Available on-site for immediate emergency first aid and triage.
- Dental Clinic: Tuesday & Thursday 8:30 AM - 3:30 PM (By appointment).
- Pharmacy Desk: Free basic over-the-counter medications (paracetamol, antacids, antihistamines, first-aid supplies).

NAVIGATION DIRECTIONS:
Walk past the Main Cafeteria towards the Gymnasium. The Clinic is located on the ground floor of the Student Center Annex building next to the Security Guard Post.
""",

    "doc_09_it_helpdesk_services.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: IT HELPDESK & CAMPUS TECH SUPPORT (ITH)
===============================================================================
Location ID: OFFICE-ITH-09
Building: Computer Studies Complex (Ground Floor, Room CSC-104)
Operating Hours: Monday - Friday: 8:00 AM - 6:00 PM; Saturday: 8:00 AM - 12:00 PM

OVERVIEW:
The IT Helpdesk assists TPC students and staff with technical issues related to campus infrastructure and digital services.

SERVICES PROVIDED:
- TPC Student Portal password resets and account unlocking.
- Official TPC Student Email (@tpc.edu.ph) onboarding and trouble-shooting.
- Campus Wi-Fi ("TPC-STUDENT-WIFI") connection authentication setup.
- Canvas Learning Management System (LMS) access support.
- Software license activation (Microsoft 365, MATLAB, Autodesk for students).

CONTACT & ONLINE SUPPORT:
Email: helpdesk@tpc.edu.ph | Phone: Ext. 404 / 405

NAVIGATION DIRECTIONS:
Located on the ground floor of the Computer Studies Complex (CSC), immediately to the left upon entering the main lobby.
""",

    "doc_10_science_research_laboratories.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: SCIENCE RESEARCH LABORATORIES (SRL)
===============================================================================
Location ID: BLDG-SRL-10
Building Name: Science Research Building
Operating Hours: Monday - Friday: 7:30 AM - 7:00 PM; Saturday: 8:00 AM - 4:00 PM

OVERVIEW:
A 3-story building dedicated to natural sciences, chemical analysis, biological research, and physics experimentations.

FLOOR DIRECTORY:
- Floor 1: General Chemistry & Organic Chemistry Labs (Rooms SRL-101, SRL-102).
- Floor 2: Biology, Microbiology & Botany Labs (Rooms SRL-201, SRL-202).
- Floor 3: Physics & Materials Science Labs (Rooms SRL-301, SRL-302).

SAFETY RULES:
- Laboratory gowns, safety goggles, and closed shoes are strictly required at all times.

NAVIGATION DIRECTIONS:
Adjacent to the Engineering & Technology Wing, north of the Central Science Quad.
""",

    "doc_11_multipurpose_gymnasium.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: MULTIPURPOSE GYMNASIUM (GYM)
===============================================================================
Location ID: BLDG-GYM-11
Building Name: TPC Sports & Multipurpose Gymnasium
Operating Hours: Monday - Saturday: 6:00 AM - 8:30 PM

OVERVIEW:
A state-of-the-art sports arena used for physical education (PE) classes, varsity practices, intramurals, university convocations, and major assemblies.

FACILITIES:
- Main Basketball & Volleyball Hardwood Court (Capacity: 2,500 spectators).
- PE Department Faculty Office (Ground Floor Room GYM-101).
- Indoor Fitness & Weight Training Gym (Second Floor Room GYM-201).
- Badminton & Table Tennis Courts (Second Floor East Annex).
- Varsity Locker Rooms & Shower Facilities (Ground Floor Rear).

NAVIGATION DIRECTIONS:
Located at the southern perimeter of the campus next to the Athletic Track Field and Student Dormitory.
""",

    "doc_12_auditorium_performing_arts.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: GRAND AUDITORIUM & PERFORMING ARTS CENTER (AUD)
===============================================================================
Location ID: BLDG-AUD-12
Building Name: TPC Grand Auditorium
Operating Hours: Open during scheduled events & rehearsals (8:00 AM - 9:00 PM)

OVERVIEW:
An 800-seat fully air-conditioned auditorium for theatrical plays, musical performances, academic symposiums, guest lectures, and graduation ceremonies.

KEY ROOMS:
- Main Hall & Stage (Floor 1 Main Entrance).
- Control Booth & Sound Light Desk (Floor 2 Mezzanine).
- Rehearsal Rooms & Dressing Rooms (Basement Level B1).
- Culture & Arts Office (Room AUD-102).

NAVIGATION DIRECTIONS:
Situated between the Main Academic Building and the University Library along Culture Way.
""",

    "doc_13_main_cafeteria_food_court.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: MAIN CAMPUS CAFETERIA & FOOD COURT (CAF)
===============================================================================
Location ID: BLDG-CAF-13
Building Name: Student Center Dining Complex
Operating Hours: Monday - Saturday: 6:30 AM - 7:30 PM

OVERVIEW:
The primary dining facility on campus offering affordable breakfast, lunch, snacks, and beverages.

STALL DIRECTORY:
- Stall 1: Rice Meals & Filipino Home Cooking (Value Meals from ₱60).
- Stall 2: Sizzling Plates & Grilled Express.
- Stall 3: Noodle House & Dimsum Counter.
- Stall 4: Fresh Fruit Juices, Smoothies & Coffee Station.
- Stall 5: Halal Certified Food Counter.
- Stall 6: Bakery, Pastries & Sandwiches.

FACILITIES:
- Seating Capacity: 600 diners.
- Microwave stations for student use.
- Automated Drinking Water Refill Stations.

NAVIGATION DIRECTIONS:
Ground floor of the Student Center, directly behind the Central Plaza fountain.
""",

    "doc_14_campus_security_headquarters.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: CAMPUS SECURITY & SAFETY HEADQUARTERS (SEC)
===============================================================================
Location ID: OFFICE-SEC-14
Building: Main Gate Entrance Complex
Operating Hours: 24 Hours a Day / 7 Days a Week

OVERVIEW:
Ensures campus physical safety, entry point validation, vehicle parking permit verification, and lost & found management.

SERVICES:
- Visitor Pass Issuance: Visitors must present a valid government-issued ID.
- Student ID Verification: Temporary gate pass issuance for forgotten IDs.
- Lost and Found Counter: Turn in or claim lost items (IDs, gadgets, umbrellas, bags).
- Emergency Assistance Hotline: Dial Extension 111 or 911 on campus landlines.

NAVIGATION DIRECTIONS:
Located immediately inside Gate 1 (Main Campus Entrance) on the right side.
""",

    "doc_15_student_council_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: SUPREME STUDENT COUNCIL & ORGANIZATIONS HUB (SSC-HUB)
===============================================================================
Location ID: OFFICE-HUB-15
Building: Student Center (2nd Floor West Wing)
Operating Hours: Monday - Friday: 8:00 AM - 6:00 PM

OVERVIEW:
Houses the Supreme Student Council (SSC), Council of Student Organizations (CSO), and official student publication ("The TPC Beacon").

KEY LOCATIONS:
- Room HUB-201: Supreme Student Council Executive Office.
- Room HUB-202: Council of Student Organizations Meeting Room.
- Room HUB-203: The TPC Beacon Editorial Board Office.
- Room HUB-204 to 210: Recognized Student Club Workspaces.

NAVIGATION DIRECTIONS:
Take the West staircase in the Student Center to the 2nd floor, turn left past the student lounge.
""",

    "doc_16_alumni_placements_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: CAREER PLACEMENT & ALUMNI RELATIONS (CAR)
===============================================================================
Location ID: OFFICE-CAR-16
Building: Administration Building (1st Floor Annex)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM

OVERVIEW:
Connects graduating students and alumni with internship programs, career fairs, job placement opportunities, and industry partnerships.

SERVICES:
- Resume & CV Review Services.
- Mock Job Interview Coaching.
- On-Campus Company Recruitment Drives.
- OJT / Internship Endorsement Letter Requests.

NAVIGATION DIRECTIONS:
Located on the 1st floor annex of the Administration Building, adjacent to Human Resources.
""",

    "doc_17_admissions_marketing_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: ADMISSIONS & RECRUITMENT OFFICE (ADM-OFF)
===============================================================================
Location ID: OFFICE-ADO-17
Building: Administration Building (Ground Floor West Wing)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM; Saturday: 8:00 AM - 12:00 PM

OVERVIEW:
Handles incoming student applications, College Entrance Examination (TPC-CAT) scheduling, transferee evaluations, and campus tours.

SERVICES:
- Freshman Admission Application Processing.
- Entrance Exam Permit Issuance.
- Credit Evaluation for Transferees.
- Campus Tour Booking.

NAVIGATION DIRECTIONS:
First door to the right upon entering the Administration Building main entrance lobby.
""",

    "doc_18_research_development_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: OFFICE OF RESEARCH & DEVELOPMENT (ORD)
===============================================================================
Location ID: OFFICE-ORD-18
Building: Science Research Building (2nd Floor Room SRL-205)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM

OVERVIEW:
Oversees faculty and student research grants, institutional ethics board clearance, patent/IP registrations, and academic journal publishing.

SERVICES:
- Institutional Ethics Review Committee (IERC) Submissions.
- Intellectual Property & Patent Application Support.
- Research Incentive Grants Processing.

NAVIGATION DIRECTIONS:
Located on the 2nd floor of the Science Research Building.
""",

    "doc_19_faculty_center_north.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: NORTH FACULTY CENTER (NFC)
===============================================================================
Location ID: BLDG-NFC-19
Building Name: North Faculty Hall
Operating Hours: Monday - Friday: 7:30 AM - 6:30 PM

OVERVIEW:
Faculty consultation hub for the College of Arts and Sciences (CAS), College of Education (COE), and General Education Department.

FACULTY DIRECTORY & CONSULTATION:
- Department of Humanities & Languages (Cubicles 1-15).
- Department of Social Sciences & Behavioral Studies (Cubicles 16-30).
- Department of Mathematics & Natural Sciences (Cubicles 31-45).

CONSULTATION HOURS PROCEDURE:
Students must book consultation slots in advance via the TPC Student Portal or check published faculty consultation schedules posted outside each cubicle block.

NAVIGATION DIRECTIONS:
North of the Main Academic Building, linked by a covered canopy walkway.
""",

    "doc_20_faculty_center_south.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: SOUTH FACULTY CENTER (SFC)
===============================================================================
Location ID: BLDG-SFC-20
Building Name: South Faculty Hall
Operating Hours: Monday - Friday: 7:30 AM - 7:00 PM; Saturday: 8:00 AM - 12:00 PM

OVERVIEW:
Faculty office facility for the College of Computer Studies (CCS) and College of Engineering (COE).

FACULTY DIRECTORY & CONSULTATION:
- Computer Science & IT Faculty Cubicles (SFC-101 to SFC-120).
- Civil & Mechanical Engineering Faculty Cubicles (SFC-201 to SFC-220).
- Electrical & Computer Engineering Faculty Cubicles (SFC-221 to SFC-240).

NAVIGATION DIRECTIONS:
Located directly between the Computer Studies Complex and the Engineering Wing.
""",

    "doc_21_campus_parking_transit.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: PARKING & TRANSPORTATION ZONES (PRK)
===============================================================================
Location ID: ZONE-PRK-21
Location: Campus Perimeter Facilities

PARKING ZONES:
- Zone A (Administration Parking): Reserved strictly for University Executives, Deans, and official university vehicles.
- Zone B (Faculty & Staff Parking): Located behind the North and South Faculty Halls (Permit Required).
- Zone C (Student Vehicle Parking): Located near Gate 3 Entrance (Requires Annual TPC Parking Sticker from Safety HQ).
- Zone D (Motorcycle & Bicycle Bay): Covered bay adjacent to the Gymnasium.

RULES:
- Speed limit inside campus is 15 km/h. Overnight parking without approval from Security HQ is strictly prohibited.

NAVIGATION DIRECTIONS:
Student parking entrance is at Gate 3 along Perimeter Road.
""",

    "doc_22_dormitory_student_housing.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: STUDENT RESIDENTIAL DORMITORY (DRM)
===============================================================================
Location ID: BLDG-DRM-22
Building Name: TPC Campus Residences
Operating Hours: Curfew at 10:00 PM daily for dormers

OVERVIEW:
On-campus housing accommodating out-of-town students in air-conditioned 2-bed and 4-bed study suites.

FACILITIES & OFFICES:
- Dorm Manager's Office (Ground Floor Lobby).
- Student Study Lounge & Kitchenette (Every floor).
- Laundry Washing Station (Basement B1).

VISITOR POLICIES:
Non-resident visitors are allowed in the Ground Floor Reception Lobby only from 1:00 PM to 6:00 PM.

NAVIGATION DIRECTIONS:
Located at the southern edge of campus behind the Multipurpose Gymnasium.
""",

    "doc_23_innovation_incubation_hub.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: INNOVATION & TECHNOLOGY INCUBATION HUB (HUB)
===============================================================================
Location ID: BLDG-HUB-23
Building Name: TPC Tech Innovation Center
Operating Hours: Monday - Friday: 8:00 AM - 8:00 PM; Saturday: 9:00 AM - 5:00 PM

OVERVIEW:
A collaborative space for student tech startups, product prototyping, AI research projects, and industry hackathons.

FACILITIES:
- Makerspace & 3D Printing Lab (Room HUB-101).
- VR/AR Immersive Experience Room (Room HUB-102).
- Startup Co-Working Space & Pitch Arena (Floor 2).
- Hardware Electronics Workstation (Room HUB-103).

NAVIGATION DIRECTIONS:
Adjacent to the Computer Studies Complex along the Science Walkway.
""",

    "doc_24_audio_visual_center.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: AUDIO-VISUAL CENTER & MULTIMEDIA SERVICES (AVC)
===============================================================================
Location ID: OFFICE-AVC-24
Building: Main Academic Building (Ground Floor Room MAB-112)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM

OVERVIEW:
Manages campus multimedia equipment loans (projectors, microphones, speakers, extension cords) for classroom lectures and student events.

EQUIPMENT LOAN PROCEDURE:
- Faculty or accredited student organization representatives must submit an AVC Requisition Form at least 24 hours prior to the event.

NAVIGATION DIRECTIONS:
Ground floor of Main Academic Building, near Audio-Visual Hall 1.
""",

    "doc_25_facilities_maintenance_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: PHYSICAL PLANT & FACILITIES MANAGEMENT (PFM)
===============================================================================
Location ID: OFFICE-PFM-25
Building: Maintenance Depot (Service Area Gate 4)
Operating Hours: Monday - Saturday: 7:00 AM - 5:00 PM

OVERVIEW:
Handles campus infrastructure repairs, air-conditioning maintenance, janitorial cleanliness, room key management, and furniture requests.

REQUESTS:
Submit maintenance work orders online via the TPC Staff Portal or at the Service Depot counter.

NAVIGATION DIRECTIONS:
Located at the rear service bay near Gate 4, behind the Engineering Annex.
""",

    "doc_26_campus_chapel_prayer_room.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: CAMPUS CHAPEL & INTERFAITH PRAYER ROOM (CHP)
===============================================================================
Location ID: BLDG-CHP-26
Building Name: Chapel of St. Lorenzo Ruiz & Interfaith Sanctuary
Operating Hours: Daily: 6:00 AM - 7:00 PM

OVERVIEW:
Provides a quiet space for spiritual reflection, prayer, and religious services for all faith communities.

SCHEDULES:
- Holy Mass: Monday - Friday 12:15 PM; Sunday 9:00 AM & 5:00 PM.
- Interfaith Quiet Prayer Room: Open daily during operational hours (Room CHP-102).

NAVIGATION DIRECTIONS:
Located in the serene garden grove west of the University Library.
""",

    "doc_27_bookstore_supply_shop.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: UNIVERSITY BOOKSTORE & MERCHANDISE SHOP (BKS)
===============================================================================
Location ID: OFFICE-BKS-27
Building: Student Center (Ground Floor North Wing)
Operating Hours: Monday - Friday: 8:00 AM - 5:30 PM; Saturday: 8:00 AM - 1:00 PM

OVERVIEW:
Official campus store selling TPC textbooks, laboratory workbooks, school uniforms, PE attire, office supplies, and official university merchandise.

SECTIONS:
- Textbook & Workbook Counter.
- School Uniform & PE Gear Fitting Counter.
- Stationeries & Art Supplies Section.
- TPC Branded Hoodies, Shirts & Souvenirs.

NAVIGATION DIRECTIONS:
Ground floor of the Student Center, right next to the Main Cafeteria entrance.
""",

    "doc_28_international_affairs_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: OFFICE FOR INTERNATIONAL LINKAGES & EXCHANGES (OIL)
===============================================================================
Location ID: OFFICE-OIL-28
Building: Administration Building (2nd Floor Room ADM-210)
Operating Hours: Monday - Friday: 8:30 AM - 4:30 PM

OVERVIEW:
Supports international exchange students, study-abroad programs, dual-degree partnerships, and student visa processing assistance.

SERVICES:
- Foreign Student Visa Extension Guidance.
- Study Abroad & Cultural Exchange Applications.
- Visiting Scholar Coordination.

NAVIGATION DIRECTIONS:
2nd floor of Administration Building, down the corridor from the President's Office.
""",

    "doc_29_community_extension_office.txt": """
===============================================================================
TPC CAMPUS DIRECTORY: COMMUNITY EXTENSION & NSTP OFFICE (CES)
===============================================================================
Location ID: OFFICE-CES-29
Building: Student Services Center (3rd Floor Room SSC-305)
Operating Hours: Monday - Friday: 8:00 AM - 5:00 PM

OVERVIEW:
Coordinates the National Service Training Program (NSTP - CWTS / LTS / ROTC), community outreach projects, and disaster risk reduction volunteer groups.

SERVICES:
- NSTP Program Enquiries & Serial Number Verification.
- Community Outreach Project Registration.
- Blood Donation & Tree Planting Activity Signups.

NAVIGATION DIRECTIONS:
3rd floor of the Student Services Center via the central elevator or stairwell.
""",

    "doc_30_tpc_faq_frequently_asked_questions.txt": """
===============================================================================
TPC CAMPUS KNOWLEDGE BASE: FREQUENTLY ASKED QUESTIONS (FAQ) & QUICK HELP
===============================================================================
Topic ID: KB-FAQ-30
Target Audience: All Students, Faculty, and Visitors

Q1: What should I do if I lost my TPC Student ID card?
A: Report immediately to Campus Security HQ at Gate 1 to get a temporary entry pass. Then proceed to the Office of the Registrar (SSC 1st Floor) to request an ID Replacement Form. Pay the replacement fee of ₱150 at the Finance Cashier Office (SSC Ground Floor).

Q2: Where can I request an official Transcript of Records (TOR) or Diploma copy?
A: Visit the Office of the Registrar located on the 1st Floor of the Student Services Center (SSC Window 1). You can also apply online through the TPC Student Portal under "Document Requests".

Q3: How do I connect my laptop or smartphone to the TPC Campus Wi-Fi?
A: Select the SSID network "TPC-STUDENT-WIFI". On the login portal page, enter your official TPC Student Portal Username (e.g. 2024-10123) and Password. If you experience login errors, visit the IT Helpdesk at CSC Room 104.

Q4: Where do I pay my tuition fee installments?
A: Pay at the Finance & Cashier Services desk on the Ground Floor East Wing of the Student Services Center. Counters accept cash, GCash, Maya, cards, and online bank transfers.

Q5: What are the library operating hours?
A: The University Library is open Monday to Friday from 7:30 AM to 7:00 PM, and Saturday from 8:00 AM to 5:00 PM.

Q6: Where is the clinic located if I feel unwell on campus?
A: The Health & Wellness Clinic is on the ground floor of the Student Center Annex, next to the Security Guard post. Medical consultations and basic medicines are free for enrolled students.

Q7: What is the campus dress code and gate policy?
A: Students must wear their official TPC Student ID at all times upon entering the campus. Casual attire is allowed, but sleeveless shirts, short shorts, and slippers are prohibited per student handbook guidelines.
"""
}

for filename, content in documents.items():
    filepath = os.path.join(RAW_DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(documents)} raw dataset text files in {RAW_DATA_DIR}.")
