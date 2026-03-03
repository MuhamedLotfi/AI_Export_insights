/* 
=============================================================================
  TITLE: Cash Flow & Collections Analysis
  DESCRIPTION: Tracks the timeline of Client Invoices to identify bottlenecks
               in cash collection leveraging vw_Customer_Project_Invoices.
  FEW-SHOT TAGS: cash flow, liquidity, collection rate, payment orders, monthly revenue
=============================================================================
*/

SELECT 
    DATE_TRUNC('month', "InvoiceDate") AS "Financial Period",
    
    -- Transaction Volume
    COUNT("InvoiceNumber") AS "Total Invoices Issued",
    
    -- Financial Realization
    SUM("TotalAfterDiscountInvoice") AS "Gross Expected Cash (EGP)",
    
    -- Collection Efficiency
    SUM(CASE WHEN "IsPaidInvoice" = true THEN "TotalAfterDiscountInvoice" ELSE 0 END) AS "Cash Collected (EGP)",
    SUM(CASE WHEN "IsPaidInvoice" = false THEN "TotalAfterDiscountInvoice" ELSE 0 END) AS "Cash Pending/Overdue (EGP)",
    
    -- Financial KPIs
    ROUND((SUM(CASE WHEN "IsPaidInvoice" = true THEN "TotalAfterDiscountInvoice" ELSE 0 END) / NULLIF(SUM("TotalAfterDiscountInvoice"), 0)) * 100, 2) AS "Collection Rate (%)"

FROM "vw_Customer_Project_Invoices"
WHERE "InvoiceDate" IS NOT NULL
GROUP BY DATE_TRUNC('month', "InvoiceDate")
ORDER BY "Financial Period" DESC;
