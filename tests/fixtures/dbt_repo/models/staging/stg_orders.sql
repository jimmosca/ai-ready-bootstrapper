with source as (
    select * from {{ source('shop', 'orders') }}
)

select
    id as order_id,
    customer_id,
    status,
    created_at
from source
