/* 
=============================================================================
  TITLE: Budget Variance & Unbilled Revenue Analysis
  DESCRIPTION: Cross-references Receiving Orders/Contracts against actual 
               Invoices generated (via vw_Customer_Project_Invoices) to find unbilled pipeline revenue.
  FEW-SHOT TAGS: budget variance, unbilled revenue, receiving orders vs invoices, EGP
=============================================================================
*/

SELECT 
    e."NameEN" AS "Client Entity",
    ro."ReceivingOrderNumber" AS "Order Number",
    
    -- Contracted / Expected Value from original orders
    COALESCE(ro."TotalPrice", 0) AS "Contracted Value (EGP)",
    
    -- Actual Invoiced (Realized) Value from Customer View
    COALESCE(SUM(cpi."TotalAfterDiscountInvoice"), 0) AS "Total Billed by Finance (EGP)",
    
    -- The Financial Gap (Unbilled Revenue)
    COALESCE(ro."TotalPrice", 0) - COALESCE(SUM(cpi."TotalAfterDiscountInvoice"), 0) AS "Unbilled Revenue (EGP)",
    
    -- Health Metric
    CASE 
        WHEN COALESCE(SUM(cpi."TotalAfterDiscountInvoice"), 0) >= COALESCE(ro."TotalPrice", 0) THEN 'Fully Billed (Closed)'
        WHEN COALESCE(SUM(cpi."TotalAfterDiscountInvoice"), 0) > 0 THEN 'Partially Billed (WIP)'
        ELSE 'Not Yet Billed (Risk)'
    END AS "Financial Status",
    
    -- Percentage Completion
    ROUND((COALESCE(SUM(cpi."TotalAfterDiscountInvoice"), 0) / NULLIF(ro."TotalPrice", 0)) * 100, 2) AS "Billing Completion (%)"

FROM "ReceivingOrders" ro
INNER JOIN "Entities" e 
    ON e."Id" = ro."AssignmentOrderId" AND e."IsDeleted" = false 
LEFT JOIN "Operations" op 
    ON ro."OperationId" = op."Id" AND op."IsDeleted" = false
LEFT JOIN vw_Customer_Project_Invoices cpi 
    ON op."OperationNumber" = cpi."ProjectNumber"

WHERE ro."IsDeleted" = false
GROUP BY 
    e."NameEN", 
    ro."ReceivingOrderNumber", 
    ro."TotalPrice"
ORDER BY "Unbilled Revenue (EGP)" DESC;
