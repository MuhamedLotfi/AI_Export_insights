/* 
=============================================================================
  TITLE: Departmental Yield & Operational Load
  DESCRIPTION: Measures the financial weight carried by each department 
               using real revenue and cost flows from the Master Views.
  FEW-SHOT TAGS: department yield, operational load, cost center, invoice ratio, efficiency
=============================================================================
*/

WITH DeptRevenue AS (
    SELECT 
        "DepartmentNameEN",
        COUNT(DISTINCT "ProjectNumber") AS "Operation_Volume",
        COUNT("InvoiceNumber") AS "Invoice_Count",
        SUM("TotalAfterDiscountInvoice") AS "Gross_Yield"
    FROM "vw_Customer_Project_Invoices"
    GROUP BY "DepartmentNameEN"
),
DeptCosts AS (
    SELECT 
        "DepartmentNameEN",
        SUM("TotalPrice") AS "Supplier_Costs"
    FROM "vw_Supplier_Project_Invoices"
    GROUP BY "DepartmentNameEN"
)

SELECT 
    r."DepartmentNameEN" AS "Department Name",
    r."Operation_Volume" AS "Total Projects Handled",
    COALESCE(r."Gross_Yield", 0) AS "Gross Revenue Yield (EGP)",
    COALESCE(c."Supplier_Costs", 0) AS "Supplier Costs (EGP)",
    
    -- Net Department Contribution
    COALESCE(r."Gross_Yield", 0) - COALESCE(c."Supplier_Costs", 0) AS "Net Department Value (EGP)",
    
    -- Efficiency Metric
    ROUND(COALESCE(r."Gross_Yield", 0) / NULLIF(r."Operation_Volume", 0), 2) AS "Avg Revenue Per Project (EGP)",
    
    -- Strategic Allocation
    CASE
        WHEN COALESCE(r."Gross_Yield", 0) - COALESCE(c."Supplier_Costs", 0) > 500000 
             THEN 'High Margin Center (Invest in Headcount)'
        WHEN r."Operation_Volume" > 50 AND COALESCE(r."Gross_Yield", 0) < COALESCE(c."Supplier_Costs", 0)
             THEN 'Loss Making Department (Audit Process)'
        ELSE 'Stable Operations'
    END AS "Board Recommendation"

FROM DeptRevenue r
LEFT JOIN DeptCosts c ON r."DepartmentNameEN" = c."DepartmentNameEN"
ORDER BY "Net Department Value (EGP)" DESC;
