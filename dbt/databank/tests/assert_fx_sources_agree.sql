-- The two FX sources (ECB API vs Marketplace) must agree within 0.5 % on common days.
-- Warn only: a disagreement means one feed is wrong, not that the pipeline must stop.
{{ config(severity='warn') }}
select rate_date, currency, ecb_api_rate, marketplace_rate, source_diff_pct
from {{ ref('int_fx_rates_daily') }}
where abs(source_diff_pct) > 0.5
