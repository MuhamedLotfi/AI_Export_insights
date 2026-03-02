/* 
=============================================================================
  TITLE: Core Business Views (Customer & Supplier)
  DESCRIPTION: Master views establishing the definitive relationships between 
               Entities, Operations, Departments, and Invoices.
  FEW-SHOT TAGS: core views, customer invoices, supplier invoices, base relationships
=============================================================================
*/

-- 1. Customer (Client) Projects & Invoices View
DROP VIEW IF EXISTS vw_customer_project_invoices;
DROP VIEW IF EXISTS "vw_Customer_Project_Invoices";
CREATE OR REPLACE VIEW "vw_Customer_Project_Invoices" AS
SELECT  
    A."InvoiceNumber",
    A."InvoiceDate",
    A."DeliveryDate" AS "InvoiceDeliveryDate",
    A."IsPaid" AS "IsPaidInvoice",
    A."TotalAmount" AS "TotalAmountInvoice",
    A."TotalAfterDiscount" AS "TotalAfterDiscountInvoice",
    A."TotalQuantity" AS "TotalQuantityInvoice",

    B."NameEN" AS "EntityName",
    B."NameAR" AS "EntityAR",
    B."TaxRegistrationNumber" AS "EntityTaxRegistrationNumber",

    ET."NameEN" AS "EntityType",
    ET."NameAR" AS "EntityTypeAR",

    C."OperationNumber" AS "ProjectNumber",
    C."OperationName" AS "ProjectName",
    -- Note: Added ProjectNameAR mapping to OperationName for consistency
    C."OperationName" AS "ProjectNameAR",
    C."OperationDate" AS "ProjectDate",

    PS."NameEN" AS "ProjectStatus",
    PS."NameAR" AS "ProjectStatusAR",

    PT."NameEN" AS "ProjectType",
    PT."NameAR" AS "ProjectTypeAR",

    C."IsPostponed" AS "IsPostponedProject",

    D."NameAR" AS "DepartmentNameAR",
    D."NameEN" AS "DepartmentNameEN"

FROM "EntityInvoices" A
LEFT JOIN "Entities" B 
    ON A."EntityId" = B."Id"
LEFT JOIN "Operations" C 
    ON C."Id" = A."OperationId"
LEFT JOIN "Departments" D 
    ON D."Id" = C."DepartmentId"
-- Lookup for Entity Type
LEFT JOIN "LookupItems" ET
    ON ET."Id" = B."EntityTypeLookupItemId"
-- Lookup for Project Status
LEFT JOIN "LookupItems" PS
    ON PS."Id" = C."StatusLookupItemId"
-- Lookup for Project Type
LEFT JOIN "LookupItems" PT
    ON PT."Id" = C."OperationTypeLookupItemId"
WHERE 
    A."IsDeleted" = false
    AND B."IsDeleted" = false
    AND C."IsDeleted" = false
    AND D."IsDeleted" = false;


-- 2. Supplier (Subcontractor/Vendor) Projects & Invoices View
DROP VIEW IF EXISTS vw_supplier_project_invoices;
DROP VIEW IF EXISTS "vw_Supplier_Project_Invoices";
CREATE OR REPLACE VIEW "vw_Supplier_Project_Invoices" AS
SELECT  
    A."CompanyInvoiceNumber" AS "SupplierInvoiceNumber",
    A."TaxRegistrationNumber" AS "SupplierTaxRegistrationNumber",
    A."TotalPaidAmount" AS "TotalPaidAmount",
    A."TotalQuantity" AS "TotalQuantity",
    A."DiscountValue" AS "DiscountValue",
    A."TotalPrice" AS "TotalPrice",
     
    C."NameEN"  AS "SupplierName",
    C."NameAR" AS "SupplierNameAR",
    -- C."TaxRegistrationNumber" AS "SupplierTaxRegistrationNumber",
    ET."NameEN" AS "SupplierType",
    ET."NameAR" AS "SupplierTypeAR",
    
    D."FiscalYear", 
    D."TenderTypeNameAR",
    D."ContractTypeNameAR",
    D."ContractNumberWithEntity",
    D."ContractDateWithEntity",
    D."ReceiptDate",
    
    E."OperationNumber" AS "ProjectNumber",
    E."OperationName" AS "ProjectName",
    E."OperationDate" AS "ProjectDate", 
    E."IsPostponed" AS "ProjectIsPostponed",

    PS."NameEN" AS "ProjectStatus",
    PS."NameAR" AS "ProjectStatusAR",

    PT."NameEN" AS "ProjectType",
    PT."NameAR" AS "ProjectTypeAR",
	 
    F."NameAR" AS "DepartmentNameAR",
    F."NameEN" AS "DepartmentNameEN"

FROM "CompanyInvoices" A
LEFT JOIN "FeeNotificationCompanies" B 
    ON A."FeeNotificationCompanyId" = B."Id"
LEFT JOIN "Entities" C 
    ON B."EntityId" = C."Id"
LEFT JOIN "FeeNotifications" D 
    ON B."FeeNotificationId" = D."Id"
LEFT JOIN "Operations" E 
    ON D."OperationId" = E."Id"
LEFT JOIN "Departments" F 
    ON E."DepartmentId" = F."Id"
-- Lookup for Entity Type
LEFT JOIN "LookupItems" ET
    ON ET."Id" = C."EntityTypeLookupItemId"
-- Lookup for Project Status
LEFT JOIN "LookupItems" PS
    ON PS."Id" = E."StatusLookupItemId"
-- Lookup for Project Type
LEFT JOIN "LookupItems" PT
    ON PT."Id" = E."OperationTypeLookupItemId"
WHERE 
    A."IsDeleted" = false  
    AND B."IsDeleted" = false
    AND C."IsDeleted" = false
    AND (ET."IsDeleted" = false OR ET."Id" IS NULL)
    AND D."IsDeleted" = false
    AND E."IsDeleted" = false
    AND F."IsDeleted" = false;
