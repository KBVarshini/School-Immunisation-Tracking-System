CREATE PROCEDURE usp_ProcessStagingData
AS
BEGIN
    -- Insert new schools if they don't exist
    INSERT INTO Schools (SchoolName, Region, IsSSP, CreatedDate)
    SELECT DISTINCT
        RawSchoolName,
        'Unknown',
        0,
        GETDATE()
    FROM StagingTable
    WHERE IsProcessed = 0
    AND RawSchoolName NOT IN (SELECT SchoolName FROM Schools);

    -- Insert new vaccine types if they don't exist
    INSERT INTO VaccineTypes (VaccineName)
    SELECT DISTINCT RawVaccineType
    FROM StagingTable
    WHERE IsProcessed = 0
    AND RawVaccineType NOT IN (SELECT VaccineName FROM VaccineTypes);

    -- Promote staged rows into VaccinationRecords
    INSERT INTO VaccinationRecords (
        SchoolID,
        VaccineID,
        VisitNumber,
        VisitDate,
        YearGroup,
        TotalEnrolled,
        TotalConsented,
        TotalVaccinated,
        VaccinatedFromPaperConsents
    )
    SELECT
        s.SchoolID,
        v.VaccineID,
        CAST(st.RawVisitNumber AS INT),
        CAST(st.RawVisitDate AS DATE),
        st.RawYearGroup,
        CAST(st.RawTotalEnrolled AS INT),
        CAST(st.RawTotalConsented AS INT),
        CAST(st.RawTotalVaccinated AS INT),
        CAST(st.RawPaperConsents AS INT)
    FROM StagingTable st
    JOIN Schools s ON s.SchoolName = st.RawSchoolName
    JOIN VaccineTypes v ON v.VaccineName = st.RawVaccineType
    WHERE st.IsProcessed = 0;

    -- Mark staged rows as processed
    UPDATE StagingTable
    SET IsProcessed = 1
    WHERE IsProcessed = 0;
END;
GO
