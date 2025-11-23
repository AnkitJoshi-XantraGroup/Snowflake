# SOGS Performance Demo Scripts

This directory contains demo scripts to showcase the capabilities of the Snowflake Optimizer & Governance Suite (SOGS), particularly the Query Explorer and Performance Advisor features.

## 📋 Files

### `performance_antipatterns_demo.sql`
Comprehensive SQL script with 20 different performance anti-patterns designed to trigger SOGS recommendations.

## 🚀 Quick Start

### Step 1: Run the Demo Script in Snowflake

```sql
-- Execute the entire script in Snowflake
-- This will:
-- 1. Create demo database and tables
-- 2. Insert sample data (650,000+ rows)
-- 3. Execute 20 anti-pattern queries
```

### Step 2: Connect SOGS to Snowflake

1. Open SOGS in your browser: `http://localhost:8000`
2. Configure Snowflake credentials using one of the authentication methods
3. Ensure your user has access to `SNOWFLAKE.ACCOUNT_USAGE` schema

### Step 3: Analyze Queries in SOGS

Navigate to the **Query Explorer** tab in SOGS and:

1. Click "Load All Queries"
2. Filter queries from database: `DEMO_PERF_TESTING`
3. Click on individual queries to see detailed analysis
4. Review the recommendations provided

## 🎯 What Each Anti-Pattern Demonstrates

### 1. **SELECT * (Selecting All Columns)**
- **Issue**: Retrieves unnecessary columns
- **Impact**: Increased data transfer, memory usage
- **Expected Recommendation**: Select only required columns
- **Detection**: Query contains `SELECT *`

### 2. **Missing WHERE Clause**
- **Issue**: Full table scan without filtering
- **Impact**: Processes entire table unnecessarily
- **Expected Recommendation**: Add WHERE clause to filter data
- **Detection**: Missing WHERE clause, large partitions scanned

### 3. **DISTINCT on Large Dataset**
- **Issue**: Requires sorting/grouping entire dataset
- **Impact**: High memory and compute usage
- **Expected Recommendation**: Use GROUP BY or add filters
- **Detection**: DISTINCT keyword with high bytes scanned

### 4. **Cartesian Join**
- **Issue**: Creates all possible combinations
- **Impact**: Exponential data growth
- **Expected Recommendation**: Add proper JOIN conditions
- **Detection**: Multiple tables in FROM without JOIN conditions

### 5. **ORDER BY Without LIMIT**
- **Issue**: Sorts entire result set
- **Impact**: Unnecessary sorting overhead
- **Expected Recommendation**: Add LIMIT or remove ORDER BY
- **Detection**: ORDER BY without LIMIT clause

### 6. **Inefficient Date Filtering**
- **Issue**: Functions on filtered columns prevent partition pruning
- **Impact**: Cannot skip irrelevant partitions
- **Expected Recommendation**: Rewrite to avoid functions on columns
- **Detection**: YEAR(), MONTH(), DATE() functions in WHERE clause

### 7. **String Operations in WHERE**
- **Issue**: LIKE with leading wildcard prevents optimization
- **Impact**: Full table scan required
- **Expected Recommendation**: Use prefix matching when possible
- **Detection**: `LIKE '%pattern'` in WHERE clause

### 8. **Multiple OR Conditions**
- **Issue**: Can prevent optimization
- **Impact**: Less efficient than IN clause
- **Expected Recommendation**: Use IN clause
- **Detection**: Multiple OR conditions with same column

### 9. **Correlated Subquery**
- **Issue**: Subquery executes for each row
- **Impact**: O(n*m) complexity
- **Expected Recommendation**: Use JOIN or window functions
- **Detection**: Subquery references outer query columns

### 10. **UNION Instead of UNION ALL**
- **Issue**: Implicit deduplication
- **Impact**: Extra processing for DISTINCT operation
- **Expected Recommendation**: Use UNION ALL if duplicates acceptable
- **Detection**: UNION keyword without ALL

### 11. **Repeated JSON Parsing**
- **Issue**: Parsing same JSON multiple times
- **Impact**: Redundant computation
- **Expected Recommendation**: Parse once using CTE
- **Detection**: Multiple references to same VARIANT path

### 12. **COUNT(DISTINCT) on High Cardinality**
- **Issue**: Memory-intensive for many unique values
- **Impact**: High memory usage
- **Expected Recommendation**: Consider APPROX_COUNT_DISTINCT
- **Detection**: COUNT(DISTINCT) with high cardinality

### 13. **NOT IN with Potential NULLs**
- **Issue**: Can cause unexpected results with NULL values
- **Impact**: Incorrect results or poor performance
- **Expected Recommendation**: Use NOT EXISTS
- **Detection**: NOT IN subquery pattern

### 14. **Multiple Passes for Aggregation**
- **Issue**: Scanning table multiple times
- **Impact**: Redundant table scans
- **Expected Recommendation**: Combine into single query
- **Detection**: Multiple similar queries in sequence

### 15. **Large Result Set Without LIMIT**
- **Issue**: Returns massive dataset to client
- **Impact**: Network transfer, client memory
- **Expected Recommendation**: Add LIMIT or pagination
- **Detection**: High rows produced without LIMIT

### 16. **Inefficient Window Function**
- **Issue**: Window function without partitioning
- **Impact**: Processes entire dataset in one partition
- **Expected Recommendation**: Add appropriate PARTITION BY
- **Detection**: Window function without PARTITION BY

### 17. **Implicit Type Conversion**
- **Issue**: Comparing different data types
- **Impact**: Forces conversion on every row
- **Expected Recommendation**: Use explicit casting
- **Detection**: Type mismatch in comparisons

### 18. **Complex CASE in WHERE**
- **Issue**: Complex logic prevents optimization
- **Impact**: Harder for optimizer to prune data
- **Expected Recommendation**: Simplify to basic predicates
- **Detection**: CASE statement in WHERE clause

### 19. **Self-Join for Comparison**
- **Issue**: Expensive join operation
- **Impact**: High memory and compute usage
- **Expected Recommendation**: Use window functions (LAG/LEAD)
- **Detection**: Self-join pattern

### 20. **COUNT Instead of EXISTS**
- **Issue**: Counts all matches instead of stopping at first
- **Impact**: Unnecessary work after finding first match
- **Expected Recommendation**: Use EXISTS
- **Detection**: COUNT in WHERE for existence check

## 📊 Expected Performance Scores

When analyzed in SOGS, these queries should receive:

- **Poor (0-40)**: Queries #1, #2, #4, #6, #9, #15 (major issues)
- **Fair (40-60)**: Queries #3, #5, #7, #11, #16 (moderate issues)
- **Good (60-80)**: Queries #8, #10, #13, #17, #18 (minor issues)

## 🔍 How to Use Query Explorer

### Analyzing Individual Queries

1. **Load Queries**: Click "Load All Queries" in Query Explorer tab
2. **Click Query Card**: Select a query to analyze
3. **Review Metrics**: See execution time, bytes scanned, partitions
4. **Check Score**: Performance score (0-100) with color coding
5. **Read Recommendations**: Detailed suggestions with:
   - Severity level (Critical, High, Medium, Low)
   - Finding description
   - Specific recommendation
   - Expected impact

### Understanding the Analysis

**Query Profile Metrics**:
- Execution time
- Bytes scanned
- Rows produced
- Partitions scanned vs. total
- Cache hit ratio
- Compilation time
- Memory spillage

**Best Practice Checks** (12+ checks):
- Result caching usage
- Partition pruning efficiency
- SELECT * usage
- WHERE clause presence
- LIMIT clause usage
- DISTINCT optimization
- JOIN conditions
- Date filtering
- String operations
- Spillage to disk
- Query complexity
- Data transfer efficiency

## 💡 Demo Presentation Tips

### For Sales/Marketing Demos

1. **Start with Impact**: Show a "Poor" scored query first
2. **Highlight Money Saved**: "This query could cost 10x more than necessary"
3. **Show Quick Wins**: Point out simple fixes like adding LIMIT
4. **Demonstrate Value**: "SOGS identified 15 issues in 2 seconds"

### For Technical Demos

1. **Show Query Profile**: Deep dive into execution metrics
2. **Explain Snowflake Concepts**: Partition pruning, micro-partitions
3. **Compare Before/After**: Run optimized version, show improvement
4. **Discuss Best Practices**: Explain why each recommendation matters

### For Executive Demos

1. **Focus on ROI**: "20% reduction in compute costs"
2. **Show Governance**: Compliance reports, security audits
3. **Highlight Automation**: "Automated recommendations vs. manual review"
4. **Demonstrate Scale**: "Analyzed 500K queries in seconds"

## 🧪 Testing Different Scenarios

### Scenario 1: Cost Optimization
Focus on queries: #2, #4, #5, #15 (high data scanning)

### Scenario 2: Performance Tuning
Focus on queries: #9, #11, #16, #19 (algorithmic improvements)

### Scenario 3: Governance & Best Practices
Focus on queries: #1, #7, #13, #18 (code quality)

## 📈 Measuring Improvement

After running the demo script:

1. Note the baseline metrics (time, bytes scanned, cost)
2. Implement recommended changes
3. Re-run queries and compare
4. Expected improvements:
   - **Query Time**: 30-90% reduction
   - **Bytes Scanned**: 50-99% reduction
   - **Cost**: Proportional to bytes scanned reduction

## 🔄 Resetting the Demo

```sql
-- Clean up demo data
DROP DATABASE DEMO_PERF_TESTING;

-- Re-run the script to start fresh
```

## 📚 Additional Resources

- **Snowflake Best Practices**: https://docs.snowflake.com/en/user-guide/ui-snowsight-best-practices
- **Query Performance**: https://docs.snowflake.com/en/user-guide/ui-query-profile
- **Optimization Guide**: https://docs.snowflake.com/en/user-guide/performance-query-optimization

## 🆘 Troubleshooting

### Issue: Queries Not Appearing in Query Explorer

**Solution**:
- Wait 5-10 minutes for ACCOUNT_USAGE to update
- Check that you're filtering by correct database
- Ensure ACCOUNT_USAGE permissions are granted

### Issue: No Recommendations Shown

**Solution**:
- Verify the query actually executed (check Snowflake history)
- Ensure query has profile data
- Check that query meets minimum execution time threshold

### Issue: Low Performance Scores for All Queries

**Solution**:
- This is expected! The demo is designed to show anti-patterns
- Use this to demonstrate SOGS value in identifying issues
- Show the "better versions" commented in the script

## 🎓 Learning Objectives

By running this demo, you'll learn:

1. **Common Snowflake anti-patterns** and their impact
2. **How SOGS identifies** performance issues automatically
3. **Best practices** for Snowflake query optimization
4. **Cost implications** of inefficient queries
5. **Quick wins** for immediate performance improvements

---

**Happy Demo-ing! 🚀**

For questions or issues, check the main README.md or TROUBLESHOOTING.md files.
