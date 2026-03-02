/* 
=============================================================================
  TITLE: End-to-End Project Lifecycle & Financial Tracker
  DESCRIPTION: Traces the originating Incoming Request (Import) through 
               Operations and binds it directly to real revenue using vw_Customer_Project_Invoices.
  FEW-SHOT TAGS: project lifecycle, import to revenue, operation flow, pipeline, conversion days
=============================================================================
*/

SELECT 
    -- 1. Incoming Stage (The Origin)
    i."ImportNumber" AS "Incoming / Request No.",
    i."ImportDate" AS "Request Date",
    e."NameEN" AS "Client Entity",
    
    -- 2. Operations Stage (The Engine)
    op."OperationNumber" AS "Project / Operation No.",
    cpi."ProjectName" AS "Operation Description",
    cpi."DepartmentNameEN" AS "Handling Department",
    
    -- 3. Invoicing Status (The Revenue in EGP directly from verified view)
    COALESCE(SUM(cpi."TotalAmountInvoice"), 0) AS "Gross Expected Invoice Value (EGP)",
    COALESCE(SUM(CASE WHEN cpi."IsPaidInvoice" = true THEN cpi."TotalAfterDiscountInvoice" ELSE 0 END), 0) AS "Realized Revenue Paid (EGP)",
    
    -- Performance Metric: Time from Request to Operations
    DATE_PART('day', op."OperationDate" - i."ImportDate") AS "Days to Activate Project",
    
    -- Health & Completion
    CASE 
        WHEN SUM(CASE WHEN cpi."IsPaidInvoice" = true THEN cpi."TotalAmountInvoice" ELSE 0 END) > 0 THEN 'Cash Realized'
        WHEN SUM(cpi."TotalAmountInvoice") > 0 THEN 'Invoiced (Pending Client Payment)'
        WHEN op."Id" IS NOT NULL THEN 'Active Operation (Unbilled)'
        ELSE 'Pending Activation'
    END AS "Lifecycle Phase"

FROM "Imports" i
INNER JOIN "Entities" e 
    ON i."EntityId" = e."Id" AND e."IsDeleted" = false
LEFT JOIN "AssignmentOrders" ao 
    ON i."Id" = ao."ImportId" AND ao."IsDeleted" = false
LEFT JOIN "ReceivingOrders" ro 
    ON ao."Id" = ro."AssignmentOrderId" AND ro."IsDeleted" = false
LEFT JOIN "Operations" op 
    ON ro."OperationId" = op."Id" AND op."IsDeleted" = false
LEFT JOIN vw_Customer_Project_Invoices cpi 
    ON op."OperationNumber" = cpi."ProjectNumber"

WHERE i."IsDeleted" = false
GROUP BY 
    i."ImportNumber", i."ImportDate", e."NameEN",
    op."OperationNumber", cpi."ProjectName", op."OperationDate",
    cpi."DepartmentNameEN", op."Id"
ORDER BY i."ImportDate" DESC;
