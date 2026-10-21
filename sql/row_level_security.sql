-- Row-Level Security: each coordinator only sees schools in their own
-- Local Health District (LHD). Admins (db_owner) see everything.
-- NOTE: all accounts below are placeholders for demonstration.

-- 1. Table mapping each database user to their LHD
CREATE TABLE LHD_UserMapping (
    UserEmail VARCHAR(100),
    LHDName   VARCHAR(100)
);

-- 2. Placeholder coordinator accounts (one per LHD)
INSERT INTO LHD_UserMapping VALUES
('coordinator.westernsydney@example.test',   'Western Sydney'),
('coordinator.sydney@example.test',          'Sydney'),
('coordinator.northernsydney@example.test',  'Northern Sydney'),
('coordinator.southeastsydney@example.test', 'South Eastern Sydney'),
('coordinator.southwestsydney@example.test', 'South Western Sydney'),
('coordinator.nepean@example.test',          'Nepean Blue Mountains'),
('coordinator.hunter@example.test',          'Hunter New England'),
('coordinator.centralcoast@example.test',    'Central Coast');
GO

-- 3. Filter function: allow db_owner, or rows matching the user's LHD
CREATE SCHEMA Security;
GO

CREATE FUNCTION Security.fn_LHD_Filter(@Region NVARCHAR(100))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT 1 AS fn_result
    WHERE
        IS_MEMBER('db_owner') = 1
        OR
        @Region IN (
            SELECT LHDName
            FROM dbo.LHD_UserMapping
            WHERE UserEmail = USER_NAME()
        )
);
GO

-- 4. Apply the policy to the Schools table
CREATE SECURITY POLICY LHD_SchoolPolicy
ADD FILTER PREDICATE Security.fn_LHD_Filter(Region)
ON dbo.Schools
WITH (STATE = ON);
GO

-- 5. Testing (replace 'test_user_1' with a real database user)
-- INSERT INTO LHD_UserMapping VALUES ('test_user_1', 'Western Sydney');
-- EXECUTE AS USER = 'test_user_1';
-- SELECT * FROM Schools;   -- should only return Western Sydney schools
-- REVERT;

