-- ============================================================================
-- SNOWFLAKE PERFORMANCE ANTI-PATTERNS DEMO SCRIPT
-- ============================================================================
-- This script contains intentionally inefficient queries to demonstrate
-- SOGS Query Explorer and Performance Advisor recommendation capabilities.
-- Run these queries in Snowflake to generate query history for analysis.
-- ============================================================================

-- SETUP: Create demo database and tables
-- ============================================================================
CREATE OR REPLACE DATABASE DEMO_PERF_TESTING;
USE DATABASE DEMO_PERF_TESTING;
USE SCHEMA PUBLIC;

-- Create sample tables with realistic data
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id INT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(20),
    created_date DATE,
    country VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(100),
    status VARCHAR(20)
);

CREATE OR REPLACE TABLE ORDERS (
    order_id INT,
    customer_id INT,
    order_date DATE,
    order_amount DECIMAL(10,2),
    order_status VARCHAR(20),
    payment_method VARCHAR(50),
    shipping_address VARCHAR(500),
    metadata VARIANT
);

CREATE OR REPLACE TABLE PRODUCTS (
    product_id INT,
    product_name VARCHAR(200),
    category VARCHAR(100),
    price DECIMAL(10,2),
    stock_quantity INT,
    supplier_id INT,
    last_updated TIMESTAMP
);

-- Insert sample data (adjust row counts as needed)
INSERT INTO CUSTOMERS
SELECT
    SEQ4() AS customer_id,
    'FirstName_' || SEQ4() AS first_name,
    'LastName_' || SEQ4() AS last_name,
    'email' || SEQ4() || '@example.com' AS email,
    '+1-555-' || LPAD(SEQ4()::VARCHAR, 7, '0') AS phone,
    DATEADD(day, -UNIFORM(1, 1000, RANDOM()), CURRENT_DATE()) AS created_date,
    CASE WHEN UNIFORM(1, 10, RANDOM()) <= 7 THEN 'USA'
         WHEN UNIFORM(1, 10, RANDOM()) <= 9 THEN 'Canada'
         ELSE 'UK' END AS country,
    'State_' || UNIFORM(1, 50, RANDOM()) AS state,
    'City_' || UNIFORM(1, 200, RANDOM()) AS city,
    CASE WHEN UNIFORM(1, 10, RANDOM()) <= 8 THEN 'Active' ELSE 'Inactive' END AS status
FROM TABLE(GENERATOR(ROWCOUNT => 100000));

INSERT INTO ORDERS
SELECT
    SEQ4() AS order_id,
    UNIFORM(1, 100000, RANDOM()) AS customer_id,
    DATEADD(day, -UNIFORM(1, 365, RANDOM()), CURRENT_DATE()) AS order_date,
    UNIFORM(10, 1000, RANDOM()) AS order_amount,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Shipped'
        WHEN 4 THEN 'Delivered'
        ELSE 'Cancelled' END AS order_status,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'PayPal'
        ELSE 'Bank Transfer' END AS payment_method,
    '123 Main St, City' || UNIFORM(1, 100, RANDOM()) AS shipping_address,
    PARSE_JSON('{"items": [{"id": ' || UNIFORM(1, 1000, RANDOM()) || ', "qty": ' || UNIFORM(1, 10, RANDOM()) || '}]}') AS metadata
FROM TABLE(GENERATOR(ROWCOUNT => 500000));

INSERT INTO PRODUCTS
SELECT
    SEQ4() AS product_id,
    'Product_' || SEQ4() AS product_name,
    'Category_' || UNIFORM(1, 20, RANDOM()) AS category,
    UNIFORM(5, 500, RANDOM()) AS price,
    UNIFORM(0, 1000, RANDOM()) AS stock_quantity,
    UNIFORM(1, 100, RANDOM()) AS supplier_id,
    DATEADD(hour, -UNIFORM(1, 720, RANDOM()), CURRENT_TIMESTAMP()) AS last_updated
FROM TABLE(GENERATOR(ROWCOUNT => 50000));


-- ============================================================================
-- ANTI-PATTERN #1: SELECT * (Selecting All Columns)
-- ============================================================================
-- Issue: Retrieves unnecessary columns, increases data transfer and memory usage
-- Expected Recommendation: Select only required columns

SELECT *
FROM CUSTOMERS
WHERE country = 'USA'
LIMIT 1000;

-- BETTER VERSION (for comparison):
-- SELECT customer_id, first_name, last_name, email
-- FROM CUSTOMERS
-- WHERE country = 'USA'
-- LIMIT 1000;


-- ============================================================================
-- ANTI-PATTERN #2: Missing WHERE Clause (Full Table Scan)
-- ============================================================================
-- Issue: Scans entire table without filtering
-- Expected Recommendation: Add WHERE clause to filter data

SELECT customer_id, first_name, last_name, email
FROM CUSTOMERS
ORDER BY created_date DESC;

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name, email
-- FROM CUSTOMERS
-- WHERE created_date >= DATEADD(month, -6, CURRENT_DATE())
-- ORDER BY created_date DESC
-- LIMIT 100;


-- ============================================================================
-- ANTI-PATTERN #3: DISTINCT on Large Dataset
-- ============================================================================
-- Issue: DISTINCT requires sorting/grouping entire dataset
-- Expected Recommendation: Use GROUP BY or add filters to reduce data volume

SELECT DISTINCT country, state, city
FROM CUSTOMERS;

-- BETTER VERSION:
-- SELECT country, state, city
-- FROM CUSTOMERS
-- GROUP BY country, state, city;


-- ============================================================================
-- ANTI-PATTERN #4: Cartesian Join (Missing JOIN Condition)
-- ============================================================================
-- Issue: Creates all possible combinations, exponential growth
-- Expected Recommendation: Add proper JOIN conditions

SELECT c.customer_id, o.order_id
FROM CUSTOMERS c, ORDERS o
WHERE c.country = 'USA'
LIMIT 100;

-- BETTER VERSION:
-- SELECT c.customer_id, o.order_id
-- FROM CUSTOMERS c
-- INNER JOIN ORDERS o ON c.customer_id = o.customer_id
-- WHERE c.country = 'USA'
-- LIMIT 100;


-- ============================================================================
-- ANTI-PATTERN #5: ORDER BY Without LIMIT
-- ============================================================================
-- Issue: Sorts entire result set unnecessarily
-- Expected Recommendation: Add LIMIT clause or remove ORDER BY if not needed

SELECT customer_id, first_name, last_name, created_date
FROM CUSTOMERS
WHERE country IN ('USA', 'Canada', 'UK')
ORDER BY created_date DESC;

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name, created_date
-- FROM CUSTOMERS
-- WHERE country IN ('USA', 'Canada', 'UK')
-- ORDER BY created_date DESC
-- LIMIT 100;


-- ============================================================================
-- ANTI-PATTERN #6: Inefficient Date Filtering (Function on Column)
-- ============================================================================
-- Issue: Functions on columns prevent partition pruning
-- Expected Recommendation: Rewrite to avoid functions on filtered columns

SELECT order_id, customer_id, order_amount
FROM ORDERS
WHERE YEAR(order_date) = 2024 AND MONTH(order_date) = 1;

-- BETTER VERSION:
-- SELECT order_id, customer_id, order_amount
-- FROM ORDERS
-- WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01';


-- ============================================================================
-- ANTI-PATTERN #7: String Operations in WHERE Clause
-- ============================================================================
-- Issue: LIKE with leading wildcard prevents index usage
-- Expected Recommendation: Use prefix matching or consider search optimization

SELECT customer_id, first_name, last_name, email
FROM CUSTOMERS
WHERE email LIKE '%@gmail.com';

-- BETTER VERSION (if looking for specific domain):
-- SELECT customer_id, first_name, last_name, email
-- FROM CUSTOMERS
-- WHERE ENDSWITH(email, '@gmail.com');


-- ============================================================================
-- ANTI-PATTERN #8: Multiple OR Conditions
-- ============================================================================
-- Issue: Multiple ORs can be inefficient, prevents optimization
-- Expected Recommendation: Use IN clause or UNION ALL

SELECT customer_id, first_name, last_name
FROM CUSTOMERS
WHERE country = 'USA' OR country = 'Canada' OR country = 'UK' OR country = 'Australia';

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name
-- FROM CUSTOMERS
-- WHERE country IN ('USA', 'Canada', 'UK', 'Australia');


-- ============================================================================
-- ANTI-PATTERN #9: Inefficient Subquery (Correlated)
-- ============================================================================
-- Issue: Correlated subquery executes for each row
-- Expected Recommendation: Use JOIN or window functions instead

SELECT c.customer_id, c.first_name, c.last_name,
    (SELECT COUNT(*) FROM ORDERS o WHERE o.customer_id = c.customer_id) AS order_count
FROM CUSTOMERS c
WHERE c.country = 'USA'
LIMIT 1000;

-- BETTER VERSION:
-- SELECT c.customer_id, c.first_name, c.last_name, COUNT(o.order_id) AS order_count
-- FROM CUSTOMERS c
-- LEFT JOIN ORDERS o ON c.customer_id = o.customer_id
-- WHERE c.country = 'USA'
-- GROUP BY c.customer_id, c.first_name, c.last_name
-- LIMIT 1000;


-- ============================================================================
-- ANTI-PATTERN #10: Inefficient UNION (Instead of UNION ALL)
-- ============================================================================
-- Issue: UNION performs deduplication (implicit DISTINCT)
-- Expected Recommendation: Use UNION ALL if duplicates are acceptable

SELECT customer_id, first_name, last_name FROM CUSTOMERS WHERE country = 'USA'
UNION
SELECT customer_id, first_name, last_name FROM CUSTOMERS WHERE country = 'Canada';

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name FROM CUSTOMERS WHERE country IN ('USA', 'Canada');
-- OR if UNION is necessary:
-- SELECT customer_id, first_name, last_name FROM CUSTOMERS WHERE country = 'USA'
-- UNION ALL
-- SELECT customer_id, first_name, last_name FROM CUSTOMERS WHERE country = 'Canada';


-- ============================================================================
-- ANTI-PATTERN #11: Inefficient JSON Parsing (Repeated)
-- ============================================================================
-- Issue: Parsing JSON multiple times in same query
-- Expected Recommendation: Parse once using CTE or subquery

SELECT
    order_id,
    metadata:items[0].id::INT AS item_id,
    metadata:items[0].qty::INT AS quantity,
    metadata:items[0].id::INT * metadata:items[0].qty::INT AS total
FROM ORDERS
WHERE metadata:items[0].id::INT > 500
LIMIT 1000;

-- BETTER VERSION:
-- WITH parsed_orders AS (
--     SELECT
--         order_id,
--         metadata:items[0].id::INT AS item_id,
--         metadata:items[0].qty::INT AS quantity
--     FROM ORDERS
-- )
-- SELECT
--     order_id,
--     item_id,
--     quantity,
--     item_id * quantity AS total
-- FROM parsed_orders
-- WHERE item_id > 500
-- LIMIT 1000;


-- ============================================================================
-- ANTI-PATTERN #12: COUNT(DISTINCT) on High Cardinality Column
-- ============================================================================
-- Issue: Can be memory-intensive for high cardinality
-- Expected Recommendation: Consider approximate COUNT DISTINCT or HyperLogLog

SELECT
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT order_id) AS unique_orders,
    COUNT(DISTINCT payment_method) AS unique_payment_methods
FROM ORDERS;

-- BETTER VERSION (if approximation acceptable):
-- SELECT
--     APPROX_COUNT_DISTINCT(customer_id) AS unique_customers,
--     APPROX_COUNT_DISTINCT(order_id) AS unique_orders,
--     COUNT(DISTINCT payment_method) AS unique_payment_methods
-- FROM ORDERS;


-- ============================================================================
-- ANTI-PATTERN #13: NOT IN with NULL values
-- ============================================================================
-- Issue: NOT IN with NULLs can cause unexpected results
-- Expected Recommendation: Use NOT EXISTS or handle NULLs explicitly

SELECT customer_id, first_name, last_name
FROM CUSTOMERS
WHERE customer_id NOT IN (SELECT customer_id FROM ORDERS);

-- BETTER VERSION:
-- SELECT c.customer_id, c.first_name, c.last_name
-- FROM CUSTOMERS c
-- WHERE NOT EXISTS (
--     SELECT 1 FROM ORDERS o WHERE o.customer_id = c.customer_id
-- );


-- ============================================================================
-- ANTI-PATTERN #14: Inefficient Aggregation (Multiple Passes)
-- ============================================================================
-- Issue: Multiple aggregations that could be combined
-- Expected Recommendation: Combine into single query

SELECT COUNT(*) AS total_orders FROM ORDERS WHERE order_status = 'Delivered';
SELECT AVG(order_amount) AS avg_amount FROM ORDERS WHERE order_status = 'Delivered';
SELECT MAX(order_date) AS max_date FROM ORDERS WHERE order_status = 'Delivered';

-- BETTER VERSION:
-- SELECT
--     COUNT(*) AS total_orders,
--     AVG(order_amount) AS avg_amount,
--     MAX(order_date) AS max_date
-- FROM ORDERS
-- WHERE order_status = 'Delivered';


-- ============================================================================
-- ANTI-PATTERN #15: Large Result Set Without Limit
-- ============================================================================
-- Issue: Returns massive dataset to client
-- Expected Recommendation: Add LIMIT or use pagination

SELECT order_id, customer_id, order_date, order_amount, order_status
FROM ORDERS
WHERE order_date >= '2024-01-01';

-- BETTER VERSION:
-- SELECT order_id, customer_id, order_date, order_amount, order_status
-- FROM ORDERS
-- WHERE order_date >= '2024-01-01'
-- ORDER BY order_date DESC
-- LIMIT 1000;


-- ============================================================================
-- ANTI-PATTERN #16: Inefficient Window Function Usage
-- ============================================================================
-- Issue: Window function without partitioning on large dataset
-- Expected Recommendation: Add appropriate partitioning

SELECT
    customer_id,
    order_id,
    order_date,
    order_amount,
    ROW_NUMBER() OVER (ORDER BY order_date) AS row_num
FROM ORDERS
LIMIT 10000;

-- BETTER VERSION:
-- SELECT
--     customer_id,
--     order_id,
--     order_date,
--     order_amount,
--     ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS row_num
-- FROM ORDERS
-- WHERE order_date >= DATEADD(month, -3, CURRENT_DATE())
-- LIMIT 10000;


-- ============================================================================
-- ANTI-PATTERN #17: Implicit Type Conversion
-- ============================================================================
-- Issue: Comparing different data types forces conversion
-- Expected Recommendation: Use explicit casting or match data types

SELECT customer_id, first_name, last_name
FROM CUSTOMERS
WHERE customer_id = '12345';  -- customer_id is INT, comparing to string

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name
-- FROM CUSTOMERS
-- WHERE customer_id = 12345;


-- ============================================================================
-- ANTI-PATTERN #18: Complex CASE in WHERE Clause
-- ============================================================================
-- Issue: Complex logic in WHERE prevents optimization
-- Expected Recommendation: Simplify or move to SELECT

SELECT customer_id, first_name, last_name, country, status
FROM CUSTOMERS
WHERE CASE
    WHEN country = 'USA' AND status = 'Active' THEN TRUE
    WHEN country = 'Canada' AND status IN ('Active', 'Pending') THEN TRUE
    WHEN country NOT IN ('USA', 'Canada') THEN TRUE
    ELSE FALSE
END;

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name, country, status
-- FROM CUSTOMERS
-- WHERE (country = 'USA' AND status = 'Active')
--    OR (country = 'Canada' AND status IN ('Active', 'Pending'))
--    OR (country NOT IN ('USA', 'Canada'));


-- ============================================================================
-- ANTI-PATTERN #19: Self-Join for Comparison
-- ============================================================================
-- Issue: Self-joins can be expensive, consider window functions
-- Expected Recommendation: Use window functions or LAG/LEAD

SELECT a.order_id, a.order_date, b.order_date AS prev_order_date
FROM ORDERS a
JOIN ORDERS b ON a.customer_id = b.customer_id
    AND b.order_date < a.order_date
WHERE a.customer_id = 12345;

-- BETTER VERSION:
-- SELECT
--     order_id,
--     order_date,
--     LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
-- FROM ORDERS
-- WHERE customer_id = 12345;


-- ============================================================================
-- ANTI-PATTERN #20: Inefficient EXISTS Check
-- ============================================================================
-- Issue: Using COUNT instead of EXISTS for existence check
-- Expected Recommendation: Use EXISTS for better performance

SELECT customer_id, first_name, last_name
FROM CUSTOMERS c
WHERE (SELECT COUNT(*) FROM ORDERS o WHERE o.customer_id = c.customer_id) > 0
LIMIT 1000;

-- BETTER VERSION:
-- SELECT customer_id, first_name, last_name
-- FROM CUSTOMERS c
-- WHERE EXISTS (SELECT 1 FROM ORDERS o WHERE o.customer_id = c.customer_id)
-- LIMIT 1000;


-- ============================================================================
-- VERIFICATION & DEMO QUERIES
-- ============================================================================

-- Get query IDs for analysis in SOGS
SELECT
    query_id,
    query_text,
    execution_status,
    total_elapsed_time/1000 AS execution_time_sec,
    bytes_scanned,
    rows_produced
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE user_name = CURRENT_USER()
    AND database_name = 'DEMO_PERF_TESTING'
    AND start_time >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 50;


-- ============================================================================
-- CLEANUP (Run after demo)
-- ============================================================================
-- DROP DATABASE DEMO_PERF_TESTING;


-- ============================================================================
-- DEMO INSTRUCTIONS
-- ============================================================================
-- 1. Run this entire script in Snowflake to create sample data
-- 2. Execute the anti-pattern queries (they will appear in query history)
-- 3. In SOGS Query Explorer, analyze these queries
-- 4. The tool will identify issues and provide recommendations
-- 5. Expected recommendations for each anti-pattern are documented above
-- ============================================================================
