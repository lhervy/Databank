-- Gold · market: conformed daily EUR reference rates with their source
select * from {{ ref('int_fx_rates_daily') }}
