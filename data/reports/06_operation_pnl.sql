/* 
=============================================================================
  TITLE: Operation Profit & Loss (P&L) Tracker
  DESCRIPTION: Calculates real profitability per Project by subtracting 
               vw_Supplier_Project_Invoices (Costs) from vw_Customer_Project_Invoices (Revenue).
  FEW-SHOT TAGS: PNL, profit and loss, operation dependencies, margin, accounts receivable, cost vs revenue
=============================================================================
*/

WITH CustomerRevenue AS (
    SELECT 
        "ProjectNumber",
        "ProjectName",
        MAX("EntityName") AS "ClientEntity",
        SUM("TotalAfterDiscountInvoice") AS "ClientRevenueEGP"
    FROM vw_Customer_Project_Invoices
    GROUP BY "ProjectNumber", "ProjectName"
),
SupplierCosts AS (
    SELECT 
        "ProjectNumber",
        SUM("TotalPrice") AS "SupplierCostEGP"
    FROM vw_Supplier_Project_Invoices
    GROUP BY "ProjectNumber"
)

SELECT 
    cr."ProjectNumber",
    cr."ProjectName",
    cr."ClientEntity",
    
    -- Revenue
    COALESCE(cr."ClientRevenueEGP", 0) AS "Gross Revenue from Client (EGP)",
    
    -- Costs
    COALESCE(sc."SupplierCostEGP", 0) AS "Gross Supplier Costs (EGP)",
    
    -- P&L / Margin
    COALESCE(cr."ClientRevenueEGP", 0) - COALESCE(sc."SupplierCostEGP", 0) AS "Net Project Profit (EGP)",
    
    -- Financial Health
    CASE
        WHEN COALESCE(cr."ClientRevenueEGP", 0) = 0 THEN 'At Risk (No Revenue)'
        WHEN COALESCE(cr."ClientRevenueEGP", 0) - COALESCE(sc."SupplierCostEGP", 0) < 0 THEN 'Loss Making Project'
        ELSE 'Profitable'
    END AS "Financial Status",

    ROUND(((COALESCE(cr."ClientRevenueEGP", 0) - COALESCE(sc."SupplierCostEGP", 0)) / NULLIF(cr."ClientRevenueEGP", 0)) * 100, 2) AS "Profit Margin (%)"

FROM CustomerRevenue cr
LEFT JOIN SupplierCosts sc ON cr."ProjectNumber" = sc."ProjectNumber"
ORDER BY "Net Project Profit (EGP)" DESC;
