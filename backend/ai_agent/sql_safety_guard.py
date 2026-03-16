import logging
import sqlglot
import sqlglot.expressions as exp

logger = logging.getLogger(__name__)

class SqlSafetyGuard:
    """
    Parses actual SQL strings into an Abstract Syntax Tree (AST) using sqlglot.
    Blocks destructive modifications and intelligently injects LIMIT clauses.
    """
    
    @classmethod
    def validate_and_patch(cls, sql: str, max_limit: int = 50) -> dict:
        """
        Parses SQL, checks for destructive commands, and auto-injects/clamps limits.
        Returns:
            {"safe": bool, "sql": str, "error": str}
        """
        try:
            # Parse the query using PostgreSQL dialect
            ast = sqlglot.parse_one(sql, read="postgres")
            
            # 1. SECURITY: Block everything except SELECT
            if not isinstance(ast, exp.Select):
                logger.warning(f"[AST GUARD] Blocked destructive query: {sql}")
                return {
                    "safe": False, 
                    "sql": sql,
                    "error": "Only SELECT/Read queries are permitted. Database modifications (INSERT/UPDATE/DELETE/DROP) are blocked for safety."
                }
            
            # 2. Extract tables used in the query for context checking
            tables_used = [t.name.lower() for t in ast.find_all(exp.Table) if t.name]
            
            # 3. PERFORMANCE: Check for WHERE clause presence
            has_where = ast.args.get("where") is not None
            
            # If querying massive tables without a WHERE filter, strictly enforce a tiny limit
            current_limit = max_limit
            huge_tables = ["entityinvoices", "paymentorders", "operations", "paymentorderclaims", "contracts", "requests"]
            if not has_where and any(t in huge_tables for t in tables_used):
                logger.info(f"[AST GUARD] Unbounded query detected on large tables {tables_used}. Clamping limit to 10.")
                current_limit = min(max_limit, 10)
            
            # 4. AST INJECTION: Automatically enforce LIMIT if missing or too high
            limit_node = ast.args.get("limit")
            
            if limit_node:
                # If they provided a LIMIT, ensure it's not larger than max_limit check
                try:
                    # Retrieve the integer value of the limit expression
                    requested_limit = int(limit_node.expression.name)
                    if requested_limit > current_limit:
                        # Replace the limit node
                        ast.set("limit", exp.Limit(expression=exp.Literal.number(current_limit)))
                except (ValueError, AttributeError):
                    # For complex limit expressions like LIMIT a * b, we gently override for safety
                    ast.set("limit", exp.Limit(expression=exp.Literal.number(current_limit)))
            else:
                # No LIMIT was provided, inject it directly into the AST syntax tree
                ast = ast.limit(current_limit)

            # Return the newly reconstructed, guaranteed-safe Postgres SQL string
            patched_sql = ast.sql(dialect="postgres")
            
            return {
                "safe": True,
                "sql": patched_sql,
                "error": None
            }

        except sqlglot.errors.ParseError as e:
            # If the LLM hallucinated invalid syntax (rare but happens), catch it before DB roundtrip
            logger.error(f"[AST GUARD] SQL syntax error detected: {e}")
            return {
                "safe": False,
                "sql": sql,
                "error": f"Invalid SQL syntax generated: {str(e)}"
            }
        except Exception as e:
            logger.error(f"[AST GUARD] Unknown error during parsing: {e}")
            return {
                "safe": False,
                "sql": sql,
                "error": f"Internal validator error: {str(e)}"
            }
