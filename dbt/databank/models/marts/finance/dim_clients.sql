{{ config(
    post_hook = [
        "{{ mask_column('first_name', 'MP_PII_TEXT') }}",
        "{{ mask_column('last_name', 'MP_PII_TEXT') }}",
        "{{ mask_column('email', 'MP_PII_TEXT') }}",
        "{{ mask_column('iban', 'MP_IBAN') }}",
        "{{ mask_column('birth_date', 'MP_BIRTH_DATE') }}"
    ]
) }}
-- Gold dimension: one row per client, current state + Banque de France credit status.
-- Personal data is masked by policy for every role except Compliance.
select
    c.client_id,
    c.first_name,
    c.last_name,
    c.email,
    c.iban,
    c.birth_date,
    c.age,
    case when c.age < 30 then '18-29' when c.age < 45 then '30-44' when c.age < 60 then '45-59' else '60+' end as age_band,
    c.city,
    c.segment,
    c.client_since,
    coalesce(cs.incident_flag, false) as has_credit_incident,
    cs.incident_type,
    cs.status_as_of                   as credit_status_as_of,
    h.version                         as cdc_version
from {{ ref('stg_core_banking__clients') }} c
left join {{ ref('int_client_credit_status') }} cs on cs.client_id = c.client_id
left join {{ ref('int_client_history') }} h on h.client_id = c.client_id and h.is_current
