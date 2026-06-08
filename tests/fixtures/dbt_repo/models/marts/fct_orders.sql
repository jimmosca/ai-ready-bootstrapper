with orders as (
    select * from {{ ref('stg_orders') }}
)

select
    order_id,
    customer_id,
    status
from orders
where status != 'cancelled'
