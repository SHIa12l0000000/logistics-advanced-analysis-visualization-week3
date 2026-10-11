# Data Dictionary — Synthetic Last-Mile Shipments

**Grain:** One row per fictional completed shipment. **Period:** 1 May–31 July 2026. **Rows:** 960. **Generation:** NumPy seeded random simulation (`scripts/generate_data.py`, default seed = 2026).

| Field | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `shipment_id` | string | SHP-00001 etc. | Unique fictional shipment identifier |
| `dispatch_date` | ISO date | YYYY-MM-DD | Fictional dispatch date |
| `zone` | category | Central, East, North, South, West, Industrial | Assigned fictional logistics zone |
| `service_level` | category | Standard, Priority | Service commitment tier |
| `traffic_level` | category | Low, Medium, High | Synthetic traffic classification |
| `weather` | category | Clear, Rain | Synthetic weather classification |
| `distance_km` | float | kilometers | Hypothetical planned distance |
| `shipment_weight_kg` | float | kilograms | Shipment mass |
| `parcel_count` | integer | parcels | Parcels for this shipment |
| `promised_hours` | float | elapsed hours | Hypothetical promised service time |
| `actual_delivery_hours` | float | elapsed hours | Hypothetical delivery completion time |
| `transport_cost_inr` | float | INR | Modelled transportation cost |

**Derived in analysis (not original columns)**

- `on_time`: `actual_delivery_hours <= promised_hours`
- `late_hours`: `max(0, actual_delivery_hours - promised_hours)`
- `sla_margin_hours`: `actual_delivery_hours - promised_hours` (negative = early)
- `weekday`: day name from `dispatch_date`

**Important:** All data and dependencies are synthetic and invented for demonstration. Costs are not real spending. No dates, names or other records represent an identified business or person. The simulator intentionally generates longer elapsed hours during congestion/rain and greater costs for long-distance trips; apparent findings are not new real-world discoveries.
