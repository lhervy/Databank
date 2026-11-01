{#
  Governance helpers used as post-hooks. dbt re-creates tables and views on
  each run, so policies are re-attached right after creation.
  The policies themselves are defined in snowflake/05_security.sql.
#}

{% macro mask_column(column, policy) -%}
    alter table {{ this }} modify column {{ column }} set masking policy DATABANK.GOVERNANCE.{{ policy }} force
{%- endmacro %}

{% macro add_client_row_policy(column='client_id') -%}
    alter view {{ this }} add row access policy DATABANK.GOVERNANCE.RAP_OWN_CLIENT_ONLY on ({{ column }})
{%- endmacro %}

{% macro fraud_score(amount, country, event_ts) -%}
    least(100,
          iff({{ amount }} > 1000, 50, 0)                  -- unusually large payment
        + iff({{ country }} <> 'FR', 30, 0)                -- abroad
        + iff(hour({{ event_ts }}) between 1 and 5, 20, 0) -- middle of the night (UTC)
    )
{%- endmacro %}
