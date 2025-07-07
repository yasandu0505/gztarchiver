from src.analyzer import classify_gazette

test_samples = [
  {"description": "Presidential Secretariat - Appointment of Hon. Nimal Siripala de Silva member of Parliament as the Minister of Ports, Shipping & Aviation from August 02, 2022", "actual": "people"},
  {"description": "Presidential Secretariat - Four Ministers under Primeminister", "actual": "people"},
  {"description": "Presidential Secretariat - Resignation of Ministers from their Offices w.e.f. January 19,2023 and appointments of Ministers from January 19, 2023", "actual": "people"},
  {"description": "Presidential Secretariat - Notification - Ministerial portfolio of Environment should be in Hon. President Charge.", "actual": "people"},
  {"description": "Presidential Secretariat - Hon. Ministers resigned from their Offices under Article 47(3)(b) of the Constitution of the Democratic Socialist Republic of Sri Lanka w.e.f. 23/10/2023 and Appointment of new Ministers w.e.f. 23/10/2023", "actual": "people"},
  {"description": "Presidential Secretariat - Appointments of Two Ministers", "actual": "people"},
  {"description": "Presidential Secretariat - Order to appoint Hon. M. Amaraweera as the Minister of Transport Service Management - Reserved", "actual": "people"},
  {"description": "Presidential Secretariat - Order to appoint Hon. Chamal Rajapaksa and 37 other M.P.'s as State Ministers, w.e.f. 27.11.2019", "actual": "people"},
  {"description": "Presidential Secretariat - Resignation and an appointment of the Minister of Information and Mass Media, w.e.f. 17.01.2020", "actual": "people"},
  {"description": "Presidential Secretariat - Order to Appoint Hon. M. Aluthgamage as the Minister of Renewable Energy & Power, w.e.f. 06.02.2020", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint Hon. Mahinda Rajapaksa Prime minister as the Minister of Community Empowerment and Eastate Infrastructure Development", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint the Ministers", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint the State Ministers", "actual": "people"},
  {"description": "Presidential Secretariat - Appointed Hon. A. Fernando and 4 others as State Ministers", "actual": "people"},
  {"description": "Presidential Secretariat - His Excellency the President has Charge Two Ministries, Ministry of Defence & Ministry of Technology. Relinquished Office of the State Ministers with effect From 26.11.2020, Appoint Hon Sarath Weerasekara, MP as Minister of Public Security with effect from 26.11.2020 - Appoint Hon. Chamal Rajapaksha MP as State Minister of National Security Home Affairs and Diaster Management with effect from 26.11.2020", "actual": "people"},
  {"description": "Presidential Secretariat - Relinquished and Appointments : State Minister of Notional Security & Disaster Management and State Minister of Home Affairs", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint Hon. Dilum Amunugama MP as State Minister of Community Police Services", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint Hon. Namal Rajapaksa, MP as State Minister of Digital Technology and Enterprise Development, w.e.f. June 03, 2021", "actual": "people"},
  {"description": "Presidential Secretariat - Relinquished Office of the Minister with effect from 08.06.2021 in Order to assume Office of the New Minister", "actual": "people"},
  {"description": "Presidential Secretariat - Relinquished Office of the State Minister with effect from 08.06.2021 in Order to assume Office of the New State Minister", "actual": "people"},
  {"description": "Presidential Secretariat - Appointed Ministers with effect from 16.08.2021 Notified the Ministers Ceased to hold the Prat Folios Previously held by then with effect from 16.08.2021", "actual": "people"},
  {"description": "Presidential Secretariat - Hon. Arundika Fernando Resigned Office of the State Minister with effect from 03.02.2022", "actual": "people"},
  {"description": "Presidential Secretariat - Removal of two Ministers from their Offices 01. Hon. Wimal Weerawansa M. P. - Minister of Industries 02. Hon. Udaya Prabath Gammanpila M. P. Minister of Energy", "actual": "people"},
  {"description": "Presidential Secretariat - Changing of Minister Posts", "actual": "people"},
  {"description": "Presidential Secretariat - Resigning Office of a State Minister (Hon. Jayantha Samaraweera)", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint Hon. Lohan Rathwaththe member of Parliment as the State Minister of Warehouse Facilities, Container yards, Port Supply Facilities and Boats and Shipping Industry Development", "actual": "people"},
  {"description": "Presidential Secretariat - Appoint Hon. Lohan Rathwaththe member of Parliment as the State Minister of Warehouse Facilities, Container yards, Port Supply Facilities and Boats and Shipping Industry Development", "actual": "people"},
  {"description": "Presidential Secretariat - Resigned of Ministers (26 Ministers)", "actual": "people"},
  {"description": "Presidential Secretariat - Removal of Jhonston Fernando, M.P. from the Post of Minister of Highways", "actual": "people"},
  {"description": "Presidential Secretariat - Hon. Dinesh Gunawardena, (M.P.) Minister of Education resigns from his Post", "actual": "people"},
  {"description": "Presidential Secretariat - Resignation of 12 State Ministers Including Hon. Chamal Rajapaksa, M.P.", "actual": "people"},
  {"description": "Presidential Secretariat - Resignation of 23 State Ministers Including Hon. Arundika Fernando", "actual": "people"},
  {"description": "Presidential Secretariat - Appointment of 22 Ministers Including Hon. Dinesh Gunawardena", "actual": "people"},
  {"description": "Presidential Secretariat - Appointment of 29 State Ministers Including Hon. Gamini Lakshman Peiris, M.P.", "actual": "people"},
  {"description": "Presidential Secretariat - Appointment of the Minister of Justice w.e.f. April 26,2022, Appointment of the State Minister of Prison Management and Prisoners' Rehabilitations w.e.f. April 26, 2022", "actual": "people"},
  {"description": "Presidential Secretariat - Appointment of Hon. Gamini Lakshman Pieris, M. P. and 03 Other Ministers from 14.05.2022", "actual": "people"},
  {"description": "Presidential Secretariat - Appointments of 09 Ministers including Hon. Nimal Siripala de Silva M.P", "actual": "people"},

  {"description": "Presidential Secretariat - Cabinet of Ministers and the Ministries and the assignment of Subjects and Functions and Departments, Public Corporations and Statutary Institutions.", "actual": "org"},
  {"description": "Presidential Secretariat - Amended Gazette Extraordinary No. 2289/43 of 22.07.2022 with effect from 16.09.2022", "actual": "org"},
  {"description": "Presidential Secretariat - Duties and Functions Amended to the Gaz. Ext. No. 2297/78 of 16.09.2022", "actual": "org"},
  {"description": "Presidential Secretariat - Amendment to the Subjects and Functions", "actual": "org"},
  {"description": "Presidential Secretariat - Amended Functions and duties from 22.12.2022", "actual": "org"},
  {"description": "Ministry of Labour - Industrial Disputes between A. Thiyagarajah Bandarawela and other part Sri Lanka Transport Board, Colombo 05 - Industrial Disputes between S. A. Kamalasena Buttala and other part Lanka Sugar Company (Pvt.) Ltd. Colombo 04", "actual": "org"},
  {"description": "Ministry of Education - Duties and Functions - Laws and Ordinance to be Implemented", "actual": "org"},
  {"description": "Presidential Secretariat - Amended Functions and Duties with effect from 30.05.2023", "actual": "org"},
  {"description": "Presidential Secretariat - Amendment of Functions and Duties", "actual": "org"},
  {"description": "Presidential Secretariat - Subject and Function of Non Cabinet minister Hon. Ranjith Siyambalapitiya State Plantation Enterprise Reforms with Effect from 23.10.2023", "actual": "org"},
  {"description": "Presidential Secretariat - Amended Functions and Duties Extra Gazette No. 2289/43 of 22 July, 2022", "actual": "org"},
  {"description": "Presidential Secretariat - Amendments of Functions and Duties", "actual": "org"},
  {"description": "Ministry of Sports and Youth Affairs - It is Hereby Announced that the Functions and tasks Institutions, Projects and Acts Mentioned in the Schedule will be Transferred to the State Minister of Sports and Youth Affairs with effect From the date 1st December 2023", "actual": "org"},
  {"description": "Presidential Secretariat - Amended Extra Gazette Extraordinary No. 2289/43 of July 22, 2022, with effect from August 23, 2024", "actual": "org"},
  {"description": "Presidential Secretariat - The Assignment of Subjects and Functions and Institutions.", "actual": "org"},
  {"description": "Presidential Secretariat - Duties and Functions", "actual": "org"},
  {"description": "Ministry of Education - Deligate Duties and Functions of the Ministry of Education to the State Minister of Education Services", "actual": "org"},
  {"description": "Ministry of Public Administration Home Affairs Provincial Council and Local Government - Subject and Functions, Departments, Public Corporations and statutory Institutions assigned to the State Ministers of the Ministry of Public Administration, Home Affairs, Provincial Councils and Local Government", "actual": "org"},
  {"description": "Ministry of Women Child Affairs and Social Security - Duties and Functions of the State Minister of Women and Child Affairs, and State Minister of Social Securit", "actual": "org"},
  {"description": "Ministry of Women & Child Affairs and Social Security - Correction Notice to the Gazette Extraordinary No. 2158/05 of 13/01/2020", "actual": "org"},
  {"description": "Presidential Secretariat - Order to Amend the Gaz.Ex.No. 2153/12 that Published the Function and duties of Ministries", "actual": "org"},
  {"description": "Presidential Secretariat - Amend the Gaz. Ex. No. 2159/15 that mentioned Functions and Duties of the Ministers", "actual": "org"},
  {"description": "Ministry of Environment and Wildlife Resources - Functions and Duties of the State Minister of Environment and Wildlife Resources", "actual": "org"},
  {"description": "Presidential Secretariat - Amend the Gaz. Ex. No. 2159/15 that mentioned Functions and Duties of the Ministers", "actual": "org"},
  {"description": "Presidential Secretariat - Subjects and Functions of the State Minister of Defence", "actual": "org"},
  {"description": "Ministry of Health & Indigenous Medical Services - Delegate duties and Functions to the State Minister of Indigenous Medical Services", "actual": "org"},
  {"description": "Presidential Secretariat - Subject & Functions of the State Minister of Renewable Energy & Power", "actual": "org"},
  {"description": "President Secretariat - Amendment, Gazette Extraordinary No. 2153/12 of 10th December 2019 Duties and Functions", "actual": "org"},
  {"description": "President Secretariat - Amendment Gazette Extraordinary No. 2153/12 of 10 th December 2019 (Duties and Functions)", "actual": "org"},
  {"description": "Presidential Secretariat - Amendment to the Gazette Extra Ordinary No. 2187/27 of 09.08.2020 : Duties & Functions", "actual": "org"},
  {"description": "Presidential Secretariat - Duties & Functions - 2020", "actual": "org"},
  {"description": "Presidential Secretariat - The Assignment of Subjects and Functions & Departments, State Corporations and Statutory Institutions to the Ministers", "actual": "org"},
  {"description": "Presidential Secretariat - The Assignment of Subjects and Functions & Departments, State Corporations and Statutory Institutions to the Ministers Amendment to the Gaz. Ex. No. 2194/74 of 25.09.2020", "actual": "org"},
  {"description": "Presidential Secretariat - The Assignment of Subjects and Functions & Departments, State Corporations and Statutory Institutions to the Ministers Amendment to the Gaz. Ex. No. 2194/74 of 25.09.2020", "actual": "org"},
  {"description": "Presidential Secretariat - Amendment to the Gazette Extra Ordinary No. 2187/27 of 09.08.2020 : Duties & Functions", "actual": "org"},
  {"description": "Presidential Secretariat - Amendment of the Subjects and Functions of the Departments, Statutory Institutions and Public Corporations", "actual": "org"},
  {"description": "Presidential Secretariat - Amendments of Functions and Duties (2187/27)", "actual": "org"},
  {"description": "Presidential Secretariat - Duties and Functions", "actual": "org"}
  
]

correct = 0



for i, sample in enumerate(test_samples):
    predicted = classify_gazette(sample["description"])
    actual = sample["actual"]
    print(f"[{i+1}] Predicted: {predicted.ljust(8)} | Actual: {actual}")
    if predicted == actual:
        correct += 1

accuracy = correct / len(test_samples)
print(f"\n✅ Accuracy: {accuracy * 100:.2f}% on {len(test_samples)} samples.")
