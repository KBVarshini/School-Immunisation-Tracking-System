
# Student Name: Brunda Varshini Katapalli

import pandas as pd
import pyodbc
import os

'''
Python will “talk” to the SQL server in the backend. So, it needs a way to communicate with the server & 
thus it uses a Driver, which acts like a translator pyodbc is a library that connects Python to the SQL Server.

'''

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    f'SERVER={os.environ["DB_SERVER"]};'
    f'DATABASE={os.environ["DB_NAME"]};'
    f'UID={os.environ["DB_USER"]};'
    f'PWD={os.environ["DB_PASSWORD"]};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

cursor = conn.cursor()


# Load dummy dataset & specify the file path for dummy dataset.
df_dummy = pd.read_csv('data/dummy_data_v2.csv')

# Clean the column names (words with spaces).
df_dummy.columns = df_dummy.columns.str.strip().str.replace(' ', '')

# Rename the columns from the dummy dataset to match the SQL insert.
df_dummy.rename(columns={

    'SubmissionTime': 'SubmissionTime',
    'Email': 'Email',
    'Year': 'Year',
    'YearGroup': 'YearGroup',
    'VaccineBeingAdministered': 'VaccineType',

    'SchoolName': 'SchoolName',
    'Suburb' : 'Suburb',
    'Postcode' : 'Postcode',
    'LocalHealthDistrict' : 'LocalHealthDistrict',
    'IsSSPSchool' : 'SSPSchool?',

    'TotalEnrolled': 'TotalEnrolled',
    'Consented(PaperandElectronic)': 'Consented(Paper&Electronic)',
    'TotalVaccinated(IncludingPaperConsents)': 'TotalVaccinated',
    'NumberVaccinated(PaperConsentsOnly)': 'PaperConsents',
    'PlannedVisits': 'PlannedVisits',

    'VisitsCompleted' : 'VisitsCompleted',
    'Visit1Date': 'Visit1Date',
    'Visit2Date': 'Visit2Date',
    'Visit3Date': 'Visit3Date',
    'Catch-UpMinExpected(ConsentedNotVaccinated)': 'ConsentedNotVaccinated',

    'Catch-UpMaxExpected(EnrolledNotVaccinated)' : 'EnrolledNotVaccinated',
    '%Consented(ofEnrolled)' : '%Consented(OfEnrolled)',
    '%Vaccinated(ofEnrolled)' : '%Vaccinated(Enrolled)',
    '%Vaccinated(ofConsented)' : '%Vaccinated(Consented)',
    'NumberVaccinated(ElectronicConsentsOnly)': 'E-Consents',

    'CoverageStatus(RAG)' : 'Coverage Status(RAG)',
    'VisitStatus' : 'VisitStatus'

}, inplace=True)

# ------------------------------------------------------------------------------ Fix NULL handling to match actual renamed columns ----------------------------------------------------------------------
df_dummy = df_dummy.fillna({
    'SchoolName':    '',
    'VaccineType':   '',
    'Visit1Date':    '',
    'Visit2Date':    '',
    'Visit3Date':    '',
    'YearGroup':     0,
    'TotalEnrolled': 0,
    'Consented(Paper&Electronic)': 0,
    'TotalVaccinated': 0,
    'PaperConsents': 0,
    'E-Consents':    0,
    'PlannedVisits': 0,
    'VisitsCompleted': 0,
    'ConsentedNotVaccinated': 0,
    'EnrolledNotVaccinated':  0,
    '%Consented(OfEnrolled)':  0.0,
    '%Vaccinated(Enrolled)':   0.0,
    '%Vaccinated(Consented)':  0.0,
    'Suburb':              '',
    'LocalHealthDistrict': '',
    'Coverage Status(RAG)': '',
    'VisitStatus':          '',
})

print("COLUMNS:", df_dummy.columns.tolist())
print(df_dummy.head())


# -------------------------------------------------------------------------------- INSERT INTO STAGING TABLE ---------------------------------------------------------------------------
# Iterates over all 3 visit dates so each visit gets its own staging row.
for _, row in df_dummy.iterrows():
    for visit_num, visit_col in enumerate(['Visit1Date', 'Visit2Date', 'Visit3Date'], start=1):
        visit_date = row[visit_col]
        if not visit_date: # Skip visits that don't exist for this record.
            continue

        cursor.execute("""
            INSERT INTO StagingTable (
                RawSchoolName,
                RawVaccineType,
                RawVisitDate,
                RawVisitNumber,
                RawYearGroup,
                RawTotalEnrolled,
                RawTotalConsented,
                RawTotalVaccinated,
                RawPaperConsents
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            row['SchoolName'],
            row['VaccineType'],
            visit_date,
            visit_num,
            row['YearGroup'],
            row['TotalEnrolled'],
            row['Consented(Paper&Electronic)'],
            row['TotalVaccinated'],
            row['PaperConsents']
        )

conn.commit()
print("Staging table insert complete.")


# ----------------------------------------------------------------------------- INSERT INTO SCHOOLS TABLE ------------------------------------------------------------------------------

unique_schools = df_dummy[['SchoolName', 'LocalHealthDistrict', 'SSPSchool?', 'Suburb', 'Postcode']].drop_duplicates()

for _, school in unique_schools.iterrows():
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM Schools WHERE SchoolName = ?)
    INSERT INTO Schools (SchoolName, Region, IsSSP, Suburb, Postcode, CreatedDate)
    VALUES (?, ?, ?, ?, ?, GETDATE())
""",
    school['SchoolName'],
    school['SchoolName'],
    school['LocalHealthDistrict'],
    int(school['SSPSchool?']),
    school['Suburb'],
    school['Postcode']
)
   

conn.commit()
print("Schools insert complete.")


# ------------------------------------------------------------------------------- INSERT INTO VACCINETYPES TABLE ---------------------------------------------------------------------
unique_vaccines = df_dummy[['VaccineType']].drop_duplicates()

for _, vax in unique_vaccines.iterrows():
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM VaccineTypes WHERE VaccineName = ?)
        INSERT INTO VaccineTypes (VaccineName)
        VALUES (?)
    """,
        vax['VaccineType'],
        vax['VaccineType']
    )

conn.commit()
print("VaccineTypes insert complete.")

# ----------------------------------------------------------------------------- INSERT INTO VACCINATIONRECORDS -----------------------------------------------------------------------
for _, row in df_dummy.iterrows():
    for visit_num, visit_col in enumerate(['Visit1Date', 'Visit2Date', 'Visit3Date'], start=1):
        visit_date = row[visit_col]
        if not visit_date:
            continue

        cursor.execute("""
    INSERT INTO VaccinationRecords (
        SchoolID,
        VaccineID,
        VisitNumber,
        VisitDate,
        YearGroup,
        TotalEnrolled,
        TotalConsented,
        TotalVaccinated,
        VaccinatedFromPaperConsents,
        SubmissionDate,
        ReportingYear,
        Email,
        PlannedVisits,
        VisitsCompleted,
        CatchUpMinExpected,
        CatchUpMaxExpected,
        ElectronicConsentVaccinated,
        VisitStatus,
        CoverageStatusRAG
    )
    SELECT
        s.SchoolID,
        v.VaccineID,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    FROM Schools s
    JOIN VaccineTypes v ON v.VaccineName = ?
    WHERE s.SchoolName = ?
""",
    visit_num,
    visit_date,
    row['YearGroup'],
    row['TotalEnrolled'],
    row['Consented(Paper&Electronic)'],
    row['TotalVaccinated'],
    row['PaperConsents'],
    row['SubmissionTime'],
   
    row['Year'],
    row['Email'],
    row['PlannedVisits'],
    row['VisitsCompleted'],
    row['ConsentedNotVaccinated'],
    row['EnrolledNotVaccinated'],
    row['E-Consents'],
    row['VisitStatus'],
    row['Coverage Status(RAG)'],
    
    # For the JOIN
    row['VaccineType'],
    row['SchoolName']
)       

conn.commit()
print("VaccinationRecords insert complete.")
