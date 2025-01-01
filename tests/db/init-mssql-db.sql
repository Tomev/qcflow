CREATE DATABASE qcflowdb;
GO

USE qcflowdb;

CREATE LOGIN qcflowuser
    WITH PASSWORD = 'Mlfl*wpassword1';
GO

CREATE USER qcflowuser FOR LOGIN qcflowuser;
GO

ALTER ROLE db_owner
    ADD MEMBER qcflowuser;
GO
