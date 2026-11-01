-- B · Merchant reference data
select merchant_id, merchant_name, category, city
from {{ source('core_banking', 'merchants') }}
