-- Part 1: Creating the Database Tables

-- Drops included to keep clean
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Customers;

-- 1. Create the Database Tables

CREATE TABLE Customers (
    CustomerID      INTEGER PRIMARY KEY,
    CustomerName    TEXT NOT NULL,
    Country         TEXT NOT NULL
);

CREATE TABLE Orders (
    OrderID         INTEGER PRIMARY KEY,
    CustomerID      INTEGER NOT NULL,
    OrderDate       TEXT NOT NULL,
    TotalAmount     REAL NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

-- 2. Insert Data into the Tables
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES
(1, 'Alice', 'USA'),
(2, 'Bob', 'UK'),
(3, 'Charlie', 'USA'),
(4, 'Diana', 'Canada'),
(5, 'Eve', 'Australia');

INSERT INTO Orders (OrderID, CustomerID, OrderDate, TotalAmount) VALUES
(101, 1, '2024-01-15', 120.50),
(102, 1, '2024-02-10', 80.00),
(103, 2, '2024-01-20', 200.00),
(104, 3, '2024-03-12', 150.00),
(105, 4, '2024-03-12', 60.00),
(106, 5, '2024-03-30', 90.00);

-- Part 2: Writing SQL Queries

-- 1. Customer Orders with Conditional Logic
SELECT c.CustomerName, c.Country, o.TotalAmount,
    CASE
        WHEN o.TotalAmount > 150    THEN 'High'
        WHEN o.TotalAmount >= 100   THEN 'Medium'
        ELSE 'Low'
    END AS OrderCategory
FROM Customers AS c 
JOIN Orders AS o ON c.CustomerID = o.CustomerID;

-- 2. Grouping and Aggregation by Country
SELECT c.Country, COUNT(o.OrderID) AS TotalOrders
FROM Customers AS c 
JOIN Orders AS o ON c.CustomerID = o.CustomerID
GROUP BY c.Country
HAVING TotalOrders > 1;

-- 3. Combining Tables with Joins
SELECT c.CustomerName, o.OrderID, o.TotalAmount
FROM Customers AS c 
LEFT JOIN Orders AS o ON c.CustomerID = o.CustomerID;

-- 4. Subqueries
SELECT c.CustomerName, o.TotalAmount
FROM Customers AS c 
JOIN Orders AS o ON c.CustomerID = o.CustomerID
WHERE o.TotalAmount > (SELECT AVG(TotalAmount) FROM Orders);
-- subquery used to average total amount

-- 5. Using a CTE for Average Order Amount

-- CTE for average spending per customer
WITH CustomerAvg AS (
    SELECT CustomerID, AVG(TotalAmount) AS AvgCustomerAmount
    FROM Orders
    GROUP BY CustomerID
),
-- CTE for average spending per country
CountryAvg AS (
    SELECT c.Country, AVG(o.TotalAmount) AS AvgCountryAmount
    FROM Customers AS c 
    JOIN Orders AS o ON c.CustomerID = o.CustomerID
    GROUP BY c.Country
)
-- Find which people spend more on average than their country
SELECT c.CustomerName, ca.AvgCustomerAmount, cy.AvgCountryAmount
FROM Customers AS c 
JOIN CustomerAvg AS ca ON c.CustomerID = ca.CustomerID
JOIN CountryAvg AS cy ON c.Country = cy.Country
WHERE ca.AvgCustomerAmount > cy.AvgCountryAmount;

-- Since there is only 1 country represented more than once it should be the higher of the two from that country.