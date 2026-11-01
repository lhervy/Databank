-- B · Clients, current state in the core banking system (PII masked at source for non-compliance roles)
select
    client_id,
    first_name,
    last_name,
    email,
    iban,
    birth_date,
    datediff(year, birth_date, current_date()) as age,
    city,
    segment,
    client_since,
    updated_at
from {{ source('core_banking', 'clients') }}
