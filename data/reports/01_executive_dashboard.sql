/* 
=============================================================================
  TITLE: Executive Financial & Operational Health Dashboard 
  DESCRIPTION: Provides High Management with a 360-degree view of Entities, 
               driven by the certified vw_Customer_Project_Invoices.
  FEW-SHOT TAGS: executive dashboard, entity summary, financial overview, total revenue, EGP
=============================================================================
*/

SELECT 
    "EntityName" AS "Client Name",
    "EntityAR" AS "الجهة / الشركة",
    COALESCE("DepartmentNameEN", 'Unassigned') AS "Responsible Department",
    
    -- Date Context
    MAX("InvoiceDate") AS "Latest Invoice Date",
    
    -- Operational Metrics
    COUNT(DISTINCT "ProjectNumber") AS "Active Projects (Operations)",
    COUNT(DISTINCT "InvoiceNumber") AS "Invoices Issued",
    
    -- Financial Metrics
    SUM(COALESCE("TotalAfterDiscountInvoice", 0)) AS "Total Invoiced Revenue (EGP)",
    SUM(CASE WHEN "IsPaidInvoice" = true THEN "TotalAfterDiscountInvoice" ELSE 0 END) AS "Collected Cash (EGP)",
    
    -- Business Weight Calculation
    CASE 
        WHEN SUM(COALESCE("TotalAfterDiscountInvoice", 0)) > 1000000 THEN 'A - Premium/High Value'
        WHEN SUM(COALESCE("TotalAfterDiscountInvoice", 0)) > 100000 THEN 'B - Medium Value'
        WHEN SUM(COALESCE("TotalAfterDiscountInvoice", 0)) > 0 THEN 'C - Standard Value'
        ELSE 'D - Operations Only'
    END AS "Account Tier"

FROM "vw_Customer_Project_Invoices"
GROUP BY "EntityName", "EntityAR", "DepartmentNameEN"
ORDER BY "Latest Invoice Date" DESC NULLS LAST;
