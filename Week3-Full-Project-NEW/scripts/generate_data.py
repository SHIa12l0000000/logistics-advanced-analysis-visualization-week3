"""Generate a fully synthetic, reproducible last-mile shipment dataset.

No records describe a real customer, carrier, or logistics company.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ZONES = ['Central', 'East', 'North', 'South', 'West', 'Industrial']


def generate(n=960, seed=2026):
    rng = np.random.default_rng(seed)
    dates = pd.date_range('2026-05-01', periods=92, freq='D')
    weekday_weights = np.array([1.10, 1.05, 1.03, 1.07, 1.20, 1.12, 0.68])
    weights = weekday_weights[dates.weekday]
    weights = weights / weights.sum()
    sampled_dates = rng.choice(dates.to_numpy(), size=n, p=weights)
    zone = rng.choice(ZONES, n, p=[.18, .16, .18, .18, .17, .13])
    service = rng.choice(['Standard', 'Priority'], n, p=[.69, .31])
    weather = rng.choice(['Clear', 'Rain'], n, p=[.79, .21])
    # Modest location-specific differences in distances and high congestion.
    base_distance = rng.gamma(shape=2.8, scale=4.0, size=n)
    zone_bias = np.array([{'Central': -2.3, 'East': .6, 'North': .2,
                           'South': 1.1, 'West': 1.8, 'Industrial': 3.2}[z]
                          for z in zone])
    distance = np.clip(base_distance + zone_bias, 1.0, 30.0)
    congestion_draw = rng.random(n)
    # Higher congestion around Central/Industrial routes.
    congested_zones = np.isin(zone, ['Central', 'Industrial'])
    p_high = .22 + .10 * congested_zones
    p_low = .29 - .05 * congested_zones
    traffic = np.where(congestion_draw < p_low, 'Low',
                       np.where(congestion_draw < 1-p_high, 'Medium', 'High'))
    weight = np.clip(rng.lognormal(mean=1.0, sigma=.65, size=n), .2, 25)
    parcels = np.clip(rng.poisson(1.3, size=n) + 1, 1, 7)
    traffic_increment = np.select([traffic == 'Medium', traffic == 'High'], [.70, 1.75], default=0.)
    rain_increment = np.where(weather == 'Rain', .77, 0.)
    zone_increment = np.where(zone == 'Industrial', .28, 0.)
    noise = rng.normal(0, .51, n)
    actual = (0.61 + .215 * distance + traffic_increment + rain_increment +
              .035 * parcels + .016 * weight + zone_increment -
              .22 * (service == 'Priority') + noise)
    actual = np.clip(actual, .65, None)
    promised = np.where(service == 'Priority', 3.55, 5.15) + .128 * distance
    cost_noise = rng.normal(0, 15, size=n)
    cost = (47 + 7.35 * distance + 2.35 * weight + 5.0 * parcels +
            11 * (traffic == 'High') + 5 * (weather == 'Rain') +
            8 * (service == 'Priority') + cost_noise)
    cost = np.clip(cost, 30, None)
    df = pd.DataFrame({
        'shipment_id': [f'SHP-{x:05d}' for x in range(1, n+1)],
        'dispatch_date': pd.to_datetime(sampled_dates).strftime('%Y-%m-%d'),
        'zone': zone,
        'service_level': service,
        'traffic_level': traffic,
        'weather': weather,
        'distance_km': np.round(distance, 2),
        'shipment_weight_kg': np.round(weight, 2),
        'parcel_count': parcels,
        'promised_hours': np.round(promised, 2),
        'actual_delivery_hours': np.round(actual, 2),
        'transport_cost_inr': np.round(cost, 2),
    })
    return df.sort_values(['dispatch_date', 'shipment_id']).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, default=960)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--output', type=Path, default=Path('data/raw/simulated_shipments.csv'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = generate(args.n, args.seed)
    data.to_csv(args.output, index=False)
    print(f'Created {len(data)} synthetic shipments in {args.output}')

if __name__ == '__main__':
    main()
