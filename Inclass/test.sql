DROP TABLE if EXISTS customers;
DROP TABLE if EXISTS orders;

.mode box
PRAGMA foreign_keys = ON;

-- table 1
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    status TEXT DEFAULT 'active'
);

-- table 2
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL,
    amount REAL CHECK (amount >= 0),
    status TEXT DEFAULT 'pending',

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);