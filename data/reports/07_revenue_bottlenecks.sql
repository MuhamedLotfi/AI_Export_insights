/* 
=============================================================================
  TITLE: Revenue Leakage & Workflow Bottleneck View
  DESCRIPTION: Aggregates total potential revenue, grouping it by the 
               current operational status using the vw_Customer_Project_Invoices baseline.
  FEW-SHOT TAGS: revenue leakage, bottleneck, stuck process, pipeline stage
=============================================================================
*/

SELECT 
    CASE 
        WHEN i."StatusLookupItemId" = 1 THEN '1. Incoming Request (Pending Review)'
        WHEN ao."Id" IS NULL THEN '2. Import Approved (Awaiting Assignment)'
        WHEN ro."Id" IS NULL THEN '3. Assigned (Awaiting Contract Execution)'
        WHEN cpi."InvoiceNumber" IS NULL THEN '4. Operation Active (Awaiting First Invoice)'
        WHEN cpi."IsPaidInvoice" = false THEN '5. Invoiced (Awaiting Client Payment)'
        ELSE '6. Cash Realized & Closed'
    END AS "Pipeline Bottleneck Stage",
    
    COUNT(DISTINCT i."Id") AS "Number of Original Requests",
    
    -- Trapped Value Metric
    SUM(COALESCE(ro."TotalPrice", cpi."TotalAmountInvoice", 0)) AS "Trapped Potential Value (EGP)",
    
    -- Actual Money collected in this stage
    SUM(CASE WHEN cpi."IsPaidInvoice" = true THEN cpi."TotalAfterDiscountInvoice" ELSE 0 END) AS "Actual Realized Cash (EGP)"

FROM "Imports" i
LEFT JOIN "AssignmentOrders" ao ON i."Id" = ao."ImportId" AND ao."IsDeleted" = false
LEFT JOIN "ReceivingOrders" ro ON ao."Id" = ro."AssignmentOrderId" AND ro."IsDeleted" = false
LEFT JOIN "Operations" op ON ro."OperationId" = op."Id" AND op."IsDeleted" = false
LEFT JOIN "vw_Customer_Project_Invoices" cpi ON op."OperationNumber" = cpi."ProjectNumber"

WHERE i."IsDeleted" = false
GROUP BY "Pipeline Bottleneck Stage"
ORDER BY "Pipeline Bottleneck Stage" ASC;
