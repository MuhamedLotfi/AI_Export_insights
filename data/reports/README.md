# Financial & Operational Reports

This directory contains advanced SQL scripts tailored for high-level management, financial analysts, and LLM implementations (as few-shot examples or semantic search context).
They focus on extracting actionable insights using EGP (Egyptian Pound) across the entire project lifecycle.

## Included Scripts

1.  **`01_executive_dashboard.sql`**
    *   **Tags:** executive dashboard, entity summary, financial overview, total revenue, EGP
    *   **Purpose:** 360-degree view of Entities, contracts, and total revenue mapped to handling departments.
2.  **`02_cash_flow_liquidity.sql`**
    *   **Tags:** cash flow, liquidity, collection rate, payment orders, monthly revenue
    *   **Purpose:** Measures the velocity of cash flow by tracking payment dates against amounts.
3.  **`03_budget_variance.sql`**
    *   **Tags:** budget variance, unbilled revenue, receiving orders vs invoices, EGP
    *   **Purpose:** Cross-references contracted values with actual generated invoices to highlight unbilled revenue.
4.  **`04_departmental_yield.sql`**
    *   **Tags:** department yield, operational load, cost center, invoice ratio, efficiency
    *   **Purpose:** Defines which departments handle the highest workload versus which departments generate actual invoiced cash.
5.  **`05_project_lifecycle_tracker.sql`**
    *   **Tags:** project lifecycle, import to revenue, operation flow, pipeline, conversion days
    *   **Purpose:** Traces operations from raw Incoming (Import) requests mapping down to the generated revenue.
6.  **`06_operation_pnl.sql`**
    *   **Tags:** PNL, profit and loss, operation dependencies, margin, accounts receivable
    *   **Purpose:** Deep dive into specific Operations, mapping expected Contract values vs Payments received and current Accounts Receivable.
7.  **`07_revenue_bottlenecks.sql`**
    *   **Tags:** revenue leakage, bottleneck, stuck process, pipeline stage
    *   **Purpose:** Visualizes where potential revenue is "stuck" (e.g., waiting for contracts, waiting for invoices, waiting for payments).

## Usage For AI Data Retrieval

When ingesting these scripts as tool examples or system prompts:
*   The `FEW-SHOT TAGS` in the SQL comment headers are ideal for embeddings matching.
*   You can extract the SQL directly, execute it against `psycopg2` using the `ERP_AI` database context.
*   The scripts rely on double-quoted camel-case identifiers (e.g., `"PaymentOrders"`) required by PostgreSQL.
