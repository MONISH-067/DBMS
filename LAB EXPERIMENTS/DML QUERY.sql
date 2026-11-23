-- DML QUERY.sql
-- DBMS Laboratory: Original SQL queries from Experiments 3 through 25
-- Name: MONISH. L
-- Register Number: 1972260035

-- ====================================================================
-- EXPERIMENT 3: DML COMMANDS USING INSERT AND SELECT
-- ====================================================================

-- 1. CREATE TABLE
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

-- 2. INSERT COMMAND
INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'ECE', 90);

-- 3. SELECT COMMAND
SELECT StudentName, Marks FROM Students
WHERE Marks >= 80;


-- ====================================================================
-- EXPERIMENT 4: DML COMMANDS USING UPDATE AND DELETE
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'ECE', 90);

-- 2. UPDATE COMMAND
UPDATE Students
SET Marks = 80
WHERE StudentID = 102;

SELECT * FROM Students;

-- 3. DELETE COMMAND
DELETE FROM Students
WHERE StudentID = 103;

SELECT * FROM Students;


-- ====================================================================
-- EXPERIMENT 5: TCL COMMANDS – COMMIT, SAVEPOINT AND ROLLBACK
-- ====================================================================

-- 1. COMMIT
CREATE TABLE Account (
    AccNo INT PRIMARY KEY,
    HolderName VARCHAR(30),
    Balance INT
);

START TRANSACTION;
INSERT INTO Account VALUES (101, 'Arun', 5000);
COMMIT;
SELECT * FROM Account;

-- 2. SAVEPOINT
START TRANSACTION;
INSERT INTO Account VALUES (102, 'Bala', 7000);
SAVEPOINT sp1;
INSERT INTO Account VALUES (103, 'Charan', 9000);
ROLLBACK TO sp1;
COMMIT;
SELECT * FROM Account;

-- 3. ROLLBACK
START TRANSACTION;
UPDATE Account
SET Balance = 6000
WHERE AccNo = 101;
ROLLBACK;
SELECT * FROM Account WHERE AccNo = 101;


-- ====================================================================
-- EXPERIMENT 6: DCL COMMANDS – GRANT AND REVOKE
-- ====================================================================

-- 1. GRANT COMMAND
CREATE DATABASE CollegeDB;
CREATE USER 'labuser'@'localhost' IDENTIFIED BY 'pass123';

GRANT SELECT, INSERT ON CollegeDB.*
TO 'labuser'@'localhost';

SHOW GRANTS FOR 'labuser'@'localhost';

-- 2. REVOKE COMMAND
REVOKE INSERT ON CollegeDB.*
FROM 'labuser'@'localhost';

SHOW GRANTS FOR 'labuser'@'localhost';


-- ====================================================================
-- EXPERIMENT 7: SELECT WITH WHERE CLAUSE AND PATTERN MATCHING
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'CSE', 90),
(104, 'David', 'ECE', 65),
(105, 'Anitha', 'CSE', 78);

-- 2. SELECT USING WHERE CLAUSE
SELECT * FROM Students
WHERE Department = 'CSE';

SELECT StudentName, Marks FROM Students
WHERE Marks >= 80;

-- 3. SELECT USING PATTERN MATCHING
SELECT * FROM Students
WHERE StudentName LIKE 'A%';

SELECT * FROM Students
WHERE StudentName LIKE '%a';


-- ====================================================================
-- EXPERIMENT 8: SELECT USING BETWEEN, IN AND AGGREGATE FUNCTIONS
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'CSE', 90),
(104, 'David', 'ECE', 65),
(105, 'Anitha', 'CSE', 78);

-- 2. SELECT USING BETWEEN
SELECT * FROM Students
WHERE Marks BETWEEN 70 AND 85;

-- 3. SELECT USING IN
SELECT * FROM Students
WHERE Department IN ('CSE', 'IT');

-- 4. AGGREGATE FUNCTIONS
SELECT COUNT(*) AS TotalStudents,
       AVG(Marks) AS AverageMarks,
       MAX(Marks) AS HighestMarks,
       MIN(Marks) AS LowestMarks,
       SUM(Marks) AS TotalMarks
FROM Students;


-- ====================================================================
-- EXPERIMENT 9: SELECT USING GROUP BY, HAVING AND ORDER BY
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'CSE', 90),
(104, 'David', 'ECE', 65),
(105, 'Anitha', 'CSE', 78),
(106, 'Farah', 'IT', 88);

-- 2. GROUP BY CLAUSE
SELECT Department, COUNT(*) AS TotalStudents
FROM Students
GROUP BY Department;

-- 3. HAVING CLAUSE
SELECT Department, AVG(Marks) AS AverageMarks
FROM Students
GROUP BY Department
HAVING AVG(Marks) > 75;

-- 4. ORDER BY CLAUSE
SELECT StudentName, Marks
FROM Students
ORDER BY Marks DESC;


-- ====================================================================
-- EXPERIMENT 10: QUERY WITH SUBQUERY AND CORRELATED QUERY
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(30),
    Department VARCHAR(15),
    Salary INT
);

INSERT INTO Employees VALUES
(101, 'Arun', 'CSE', 50000),
(102, 'Bala', 'IT', 40000),
(103, 'Charan', 'CSE', 60000),
(104, 'David', 'ECE', 45000),
(105, 'Anitha', 'IT', 55000),
(106, 'Farah', 'ECE', 65000);

-- 2. SUBQUERY
SELECT EmpName, Salary
FROM Employees
WHERE Salary > (SELECT AVG(Salary) FROM Employees);

-- 3. CORRELATED QUERY
SELECT E1.EmpName, E1.Department, E1.Salary
FROM Employees E1
WHERE E1.Salary > (
    SELECT AVG(E2.Salary)
    FROM Employees E2
    WHERE E2.Department = E1.Department
);


-- ====================================================================
-- EXPERIMENT 11: QUERY WITH JOINS – EQUIJOIN, INNER JOIN AND OUTER JOIN
-- ====================================================================

-- 1. CREATE TABLES AND INSERT VALUES
CREATE TABLE Departments (DeptID INT PRIMARY KEY, DeptName VARCHAR(20));
INSERT INTO Departments VALUES (1, 'CSE'), (2, 'IT'), (3, 'ECE');

CREATE TABLE Employees (EmpID INT PRIMARY KEY, EmpName VARCHAR(20), DeptID INT);
INSERT INTO Employees VALUES (101, 'Arun', 1), (102, 'Bala', 2),
(103, 'Charan', 1), (104, 'David', 4);

-- 2. EQUIJOIN
SELECT E.EmpName, D.DeptName
FROM Employees E, Departments D
WHERE E.DeptID = D.DeptID;

-- 3. INNER JOIN
SELECT E.EmpName, D.DeptName
FROM Employees E INNER JOIN Departments D
ON E.DeptID = D.DeptID;

-- 4. LEFT OUTER JOIN
SELECT E.EmpName, D.DeptName
FROM Employees E LEFT OUTER JOIN Departments D
ON E.DeptID = D.DeptID;


-- ====================================================================
-- EXPERIMENT 12: QUERY WITH VIEW AND INDEX
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10),
    Marks INT
);

INSERT INTO Students VALUES
(101, 'Arun', 'CSE', 85),
(102, 'Bala', 'IT', 72),
(103, 'Charan', 'CSE', 90);

-- 2. CREATE AND USE VIEW
CREATE VIEW CSEStudents AS
SELECT StudentID, StudentName, Marks
FROM Students WHERE Department = 'CSE';

SELECT * FROM CSEStudents;

-- 3. CREATE INDEX
CREATE INDEX idx_department ON Students(Department);
SHOW INDEX FROM Students;

-- 4. DROP INDEX AND DROP VIEW
DROP INDEX idx_department ON Students;
DROP VIEW CSEStudents;


-- ====================================================================
-- EXPERIMENT 13: QUERY WITH AUTO_INCREMENT SEQUENCES
-- ====================================================================

-- 1. CREATE TABLE WITH AUTO_INCREMENT
CREATE TABLE Students (
    StudentID INT AUTO_INCREMENT PRIMARY KEY,
    StudentName VARCHAR(30),
    Department VARCHAR(10)
);

INSERT INTO Students (StudentName, Department) VALUES
('Arun', 'CSE'), ('Bala', 'IT'), ('Charan', 'ECE');

SELECT * FROM Students;

-- 2. AUTO_INCREMENT IN ANOTHER TABLE
CREATE TABLE Products (
    ProductID INT AUTO_INCREMENT PRIMARY KEY,
    ProductName VARCHAR(30)
);

INSERT INTO Products (ProductName) VALUES ('Pen');
INSERT INTO Products (ProductName) VALUES ('Book');
SELECT * FROM Products;


-- ====================================================================
-- EXPERIMENT 14: SIMPLE PROGRAMMING USING REPEAT AND WHILE
-- ====================================================================

-- 1. REPEAT LOOP
DELIMITER //
CREATE PROCEDURE RepeatExample()
BEGIN
    DECLARE i INT DEFAULT 1;
    REPEAT
        SELECT i;
        SET i = i + 1;
    UNTIL i > 3
    END REPEAT;
END //
DELIMITER ;
CALL RepeatExample();

-- 2. WHILE LOOP
DELIMITER //
CREATE PROCEDURE WhileExample()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 3 DO
        SELECT i;
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL WhileExample();


-- ====================================================================
-- EXPERIMENT 15: SIMPLE PROGRAMMING USING CASE AND LOOP
-- ====================================================================

-- 1. CASE STATEMENT
SELECT StudentName, Marks,
CASE
    WHEN Marks >= 85 THEN 'A'
    WHEN Marks >= 70 THEN 'B'
    ELSE 'C'
END AS Grade
FROM Students;

-- 2. LOOP STATEMENT
DELIMITER //
CREATE PROCEDURE LoopExample()
BEGIN
    DECLARE i INT DEFAULT 1;
    myloop: LOOP
        SELECT i;
        SET i = i + 1;
        IF i > 3 THEN
            LEAVE myloop;
        END IF;
    END LOOP myloop;
END //
DELIMITER ;
CALL LoopExample();


-- ====================================================================
-- EXPERIMENT 16: HIGH LEVEL PROGRAMMING EXTENSIONS – PROCEDURES
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(30),
    Department VARCHAR(15),
    Salary INT
);

INSERT INTO Employees VALUES
(101, 'Arun', 'CSE', 50000),
(102, 'Bala', 'IT', 40000),
(103, 'Charan', 'CSE', 60000);

-- 2. CREATE AND CALL A STORED PROCEDURE
DELIMITER //
CREATE PROCEDURE GetEmployees(IN dept VARCHAR(15))
BEGIN
    SELECT EmpID, EmpName, Salary
    FROM Employees
    WHERE Department = dept;
END //
DELIMITER ;

CALL GetEmployees('CSE');


-- ====================================================================
-- EXPERIMENT 17: HIGH LEVEL PROGRAMMING EXTENSIONS – FUNCTION
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(30),
    Salary DECIMAL(10,2)
);

INSERT INTO Employees VALUES
(101, 'Arun', 50000),
(102, 'Bala', 40000),
(103, 'Charan', 60000);

-- 2. CREATE AND CALL A FUNCTION
DELIMITER //
CREATE FUNCTION CalculateBonus(sal DECIMAL(10,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    RETURN sal * 0.10;
END //
DELIMITER ;

SELECT EmpName, Salary, CalculateBonus(Salary) AS Bonus
FROM Employees;


-- ====================================================================
-- EXPERIMENT 18: HIGH LEVEL PROGRAMMING EXTENSIONS – CURSORS
-- ====================================================================

-- 1. CREATE TABLE AND INSERT VALUES
CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(30),
    Salary INT
);

INSERT INTO Employees VALUES
(101, 'Arun', 50000),
(102, 'Bala', 40000),
(103, 'Charan', 60000);

-- 2. CREATE AND USE A CURSOR
DELIMITER //
CREATE PROCEDURE DisplayEmployees()
BEGIN
    DECLARE finished INT DEFAULT 0;
    DECLARE emp_name VARCHAR(30);
    DECLARE emp_cursor CURSOR FOR
        SELECT EmpName FROM Employees;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished = 1;

    OPEN emp_cursor;
    read_loop: LOOP
        FETCH emp_cursor INTO emp_name;
        IF finished = 1 THEN
            LEAVE read_loop;
        END IF;
        SELECT emp_name AS EmpName;
    END LOOP;
    CLOSE emp_cursor;
END //
DELIMITER ;

CALL DisplayEmployees();


-- ====================================================================
-- EXPERIMENT 19: HIGH LEVEL PROGRAMMING EXTENSIONS – TRIGGERS
-- ====================================================================

-- 1. CREATE TABLES
CREATE TABLE EmployeeLog (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    EmpName VARCHAR(30),
    ActionType VARCHAR(20)
);

CREATE TABLE Employees (
    EmpID INT PRIMARY KEY,
    EmpName VARCHAR(30)
);

-- 2. CREATE AND TEST A TRIGGER
DELIMITER //
CREATE TRIGGER after_employee_insert
AFTER INSERT ON Employees
FOR EACH ROW
BEGIN
    INSERT INTO EmployeeLog (EmpName, ActionType)
    VALUES (NEW.EmpName, 'INSERTED');
END //
DELIMITER ;

INSERT INTO Employees VALUES (101, 'Arun');
SELECT * FROM EmployeeLog;


-- ====================================================================
-- EXPERIMENT 20: MYSQL STRING FUNCTIONS – REPLACE, REPEAT, REVERSE, RIGHT, LEFT, RPAD, LPAD
-- ====================================================================

-- 1. STRING FUNCTIONS
SELECT
    REPLACE('DATABASE', 'DATA', 'SQL') AS Replaced,
    REPEAT('Hi', 3) AS Repeated,
    REVERSE('MYSQL') AS Reversed,
    RIGHT('COMPUTER', 4) AS RightPart,
    LEFT('COMPUTER', 4) AS LeftPart;

-- 2. RPAD AND LPAD FUNCTIONS
SELECT
    RPAD('SQL', 6, '*') AS RightPadded,
    LPAD('SQL', 6, '*') AS LeftPadded;


-- ====================================================================
-- EXPERIMENT 21: MYSQL STRING FUNCTIONS – PART II
-- ====================================================================

-- SQL Commands
SELECT CONCAT('[',SPACE(5),']') AS SpaceValue;
SELECT SUBSTR('DATABASE',1,8) AS SubString;
SELECT UPPER('mysql') AS UpperText;
SELECT LOWER('DATABASE') AS LowerText;
SELECT TRIM('   DBMS   ') AS TrimmedText;
SELECT LENGTH('DBMS') AS StringLength;

-- Combined Query
SELECT CONCAT('[',SPACE(5),']') AS SpaceValue, SUBSTR('DATABASE',1,8) AS SubString,
UPPER('mysql') AS UpperText, LOWER('DATABASE') AS LowerText,
TRIM('   DBMS   ') AS TrimmedText, LENGTH('DBMS') AS StringLength;


-- ====================================================================
-- EXPERIMENT 22: DATABASE CONNECTIVITY USING PHP AND MYSQL
-- ====================================================================

-- Create Database and Table
CREATE DATABASE college;
USE college;
CREATE TABLE Student (StudentID INT PRIMARY KEY, StudentName VARCHAR(40), Department VARCHAR(20));
INSERT INTO Student VALUES (1,'Asha','CSE'),(2,'Rahim','IT');

-- PHP Program (save as display.php)
-- SQL extracted from the PHP $sql string in the source document.
SELECT StudentID, StudentName, Department FROM Student;


-- ====================================================================
-- EXPERIMENT 23: TRAIN TICKET RESERVATION SYSTEM
-- ====================================================================

-- Create Database and Tables
CREATE DATABASE TrainReservation;
USE TrainReservation;
CREATE TABLE Train (TrainID INT PRIMARY KEY, TrainName VARCHAR(50), Source VARCHAR(30), Destination VARCHAR(30), AvailableSeats INT CHECK (AvailableSeats>=0));
CREATE TABLE Passenger (PassengerID INT PRIMARY KEY, Name VARCHAR(40) NOT NULL, TrainID INT, JourneyDate DATE, FOREIGN KEY (TrainID) REFERENCES Train(TrainID));

-- Insert Sample Data
INSERT INTO Train VALUES (12623,'Chennai Express','Chennai','Bengaluru',50);
INSERT INTO Passenger VALUES (101,'Arjun',12623,'2026-12-10'),(102,'Sara',12623,'2026-12-10');

-- Queries
SELECT * FROM Passenger;
SELECT TrainName, AvailableSeats FROM Train;
SELECT T.TrainName,P.Name,P.JourneyDate FROM Train T JOIN Passenger P ON T.TrainID=P.TrainID;


-- ====================================================================
-- EXPERIMENT 24: COLLEGE ADMISSION FORM
-- ====================================================================

-- Create Database and Table
CREATE DATABASE CollegeAdmission;
USE CollegeAdmission;
CREATE TABLE Applicant (ApplicantID INT PRIMARY KEY, ApplicantName VARCHAR(50) NOT NULL, DateOfBirth DATE, Marks DECIMAL(5,2) CHECK (Marks BETWEEN 0 AND 100), Course VARCHAR(20) NOT NULL, Phone VARCHAR(15) UNIQUE);

-- Insert Applicant Details
INSERT INTO Applicant VALUES (1,'Nithya','2007-04-12',92,'CSE','9876501234'),(2,'Imran','2007-09-21',85,'IT','9876505678');

-- Queries
SELECT * FROM Applicant;
SELECT ApplicantName,Marks FROM Applicant WHERE Marks>=90;
SELECT COUNT(*) AS TotalApplicants FROM Applicant;
SELECT Course,COUNT(*) AS Applicants FROM Applicant GROUP BY Course;


-- ====================================================================
-- EXPERIMENT 25: QR ENABLED AUTOMATIC BUS TICKET BOOKING SYSTEM
-- ====================================================================

-- Create Database and Tables
CREATE DATABASE QRBusBooking;
USE QRBusBooking;
CREATE TABLE Bus (BusID INT PRIMARY KEY, Route VARCHAR(60), Fare DECIMAL(7,2) NOT NULL);
CREATE TABLE Passenger (PassengerID INT PRIMARY KEY, PassengerName VARCHAR(50) NOT NULL);
CREATE TABLE Booking (BookingID INT PRIMARY KEY, BusID INT NOT NULL, PassengerID INT NOT NULL, BookingDate DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(BusID) REFERENCES Bus(BusID), FOREIGN KEY(PassengerID) REFERENCES Passenger(PassengerID));

-- Insert Sample Data
INSERT INTO Bus VALUES (21,'Central Station - Airport',45.00);
INSERT INTO Passenger VALUES (1001,'Aarav'),(1002,'Meera');
INSERT INTO Booking (BookingID,BusID,PassengerID) VALUES (501,21,1001),(502,21,1002);

-- Booking and QR Payload Queries
SELECT B.BookingID,P.PassengerName,S.Route,S.Fare FROM Booking B JOIN Passenger P ON B.PassengerID=P.PassengerID JOIN Bus S ON B.BusID=S.BusID;
SELECT CONCAT('BOOKING=',BookingID,'; BUS=',BusID,'; PASSENGER=',PassengerID) AS QR_Payload FROM Booking WHERE BookingID=501;
