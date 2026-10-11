"""Reproducible Week 3 logistics EDA and Matplotlib visualizations.

Usage: python scripts/analyze_logistics.py --input data/raw/simulated_shipments.csv
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NUMERIC = ['distance_km', 'shipment_weight_kg', 'parcel_count',
           'promised_hours', 'actual_delivery_hours', 'transport_cost_inr']
REQUIRED = ['shipment_id', 'dispatch_date', 'zone', 'service_level',
            'traffic_level', 'weather', *NUMERIC]


def read_and_validate(path: Path):
    df = pd.read_csv(path)
    missing_columns = set(REQUIRED) - set(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    if df[REQUIRED].isna().any().any():
        raise ValueError('Missing values found; clean input before EDA')
    if df['shipment_id'].duplicated().any():
        raise ValueError('Duplicate shipment IDs found')
    df['dispatch_date'] = pd.to_datetime(df['dispatch_date'], errors='raise')
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors='raise')
    for col in NUMERIC:
        if not np.isfinite(df[col]).all():
            raise ValueError(f'Non-finite values in {col}')
    if (df[NUMERIC] <= 0).any().any():
        raise ValueError('Numeric logistics measures must be positive')
    df['late_hours'] = (df['actual_delivery_hours'] - df['promised_hours']).clip(lower=0)
    df['sla_margin_hours'] = df['actual_delivery_hours'] - df['promised_hours']
    df['on_time'] = df['actual_delivery_hours'] <= df['promised_hours']
    df['weekday'] = df['dispatch_date'].dt.day_name()
    return df


def write_results(df: pd.DataFrame, output: Path):
    out_tables = output / 'tables'
    figs = output / 'figures'
    out_tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    # Overall descriptive statistics and frequency tables.
    descriptive = df[NUMERIC + ['late_hours', 'sla_margin_hours']].describe().round(3)
    descriptive.to_csv(out_tables / 'descriptive_statistics.csv')
    zone = df.groupby('zone', sort=True).agg(
        shipments=('shipment_id', 'count'),
        on_time_rate=('on_time', 'mean'),
        mean_delivery_hours=('actual_delivery_hours', 'mean'),
        mean_distance_km=('distance_km', 'mean'),
        average_cost_inr=('transport_cost_inr', 'mean'),
        total_cost_inr=('transport_cost_inr', 'sum'),
    ).reset_index()
    zone['on_time_pct'] = (zone['on_time_rate'] * 100).round(2)
    zone.round(3).to_csv(out_tables / 'zone_kpis.csv', index=False)
    traffic = df.groupby('traffic_level').agg(
        shipments=('shipment_id', 'count'), on_time_rate=('on_time', 'mean'),
        mean_sla_margin_hours=('sla_margin_hours', 'mean'),
        median_sla_margin_hours=('sla_margin_hours', 'median'),
    ).reindex(['Low', 'Medium', 'High']).reset_index()
    traffic['on_time_pct'] = 100 * traffic['on_time_rate']
    traffic.round(3).to_csv(out_tables / 'traffic_kpis.csv', index=False)
    service = df.groupby('service_level').agg(shipments=('shipment_id','count'),
        on_time_rate=('on_time','mean'), average_cost_inr=('transport_cost_inr','mean'))
    service.round(3).to_csv(out_tables / 'service_level_kpis.csv')
    weather = df.groupby('weather').agg(shipments=('shipment_id','count'),
        on_time_rate=('on_time','mean'), avg_delivery_hours=('actual_delivery_hours','mean'))
    weather.round(3).to_csv(out_tables / 'weather_kpis.csv')
    daily = df.set_index('dispatch_date').resample('D').agg(
        shipments=('shipment_id','count'), total_transport_cost_inr=('transport_cost_inr','sum'))
    daily['shipments_7day_mean'] = daily['shipments'].rolling(7, min_periods=1).mean()
    daily.to_csv(out_tables / 'daily_volume.csv')
    correlation_columns = ['distance_km', 'shipment_weight_kg', 'parcel_count',
                           'actual_delivery_hours', 'transport_cost_inr', 'sla_margin_hours']
    corr = df[correlation_columns].corr(method='pearson')
    corr.round(4).to_csv(out_tables / 'correlations_pearson.csv')
    metrics = {
        'data_type': 'synthetic_demonstration_not_real_company_data',
        'number_of_shipments': int(len(df)),
        'first_date': df['dispatch_date'].min().strftime('%Y-%m-%d'),
        'last_date': df['dispatch_date'].max().strftime('%Y-%m-%d'),
        'unique_days_with_shipments': int(df['dispatch_date'].nunique()),
        'calendar_days_in_window': int(len(daily)),
        'mean_delivery_hours': round(float(df['actual_delivery_hours'].mean()), 3),
        'median_delivery_hours': round(float(df['actual_delivery_hours'].median()), 3),
        'std_delivery_hours': round(float(df['actual_delivery_hours'].std()), 3),
        'p90_delivery_hours': round(float(df['actual_delivery_hours'].quantile(.9)), 3),
        'mode_rounded_delivery_hours': float(df['actual_delivery_hours'].round(0).mode().iat[0]),
        'mean_cost_inr': round(float(df['transport_cost_inr'].mean()), 2),
        'median_cost_inr': round(float(df['transport_cost_inr'].median()), 2),
        'total_cost_inr': round(float(df['transport_cost_inr'].sum()), 2),
        'on_time_pct': round(float(df['on_time'].mean()*100), 2),
        'late_count': int((~df['on_time']).sum()),
        'daily_avg_volume': round(float(daily['shipments'].mean()), 2),
        'daily_peak_volume': int(daily['shipments'].max()),
        'mean_distance_km': round(float(df['distance_km'].mean()), 2),
        'distance_cost_pearson_r': round(float(corr.loc['distance_km','transport_cost_inr']), 3),
        'distance_delivery_pearson_r': round(float(corr.loc['distance_km','actual_delivery_hours']), 3),
        'sla_margin_delivery_corr': round(float(corr.loc['sla_margin_hours','actual_delivery_hours']),3),
        'slowest_zone': str(zone.loc[zone['mean_delivery_hours'].idxmax(), 'zone']),
        'lowest_on_time_zone': str(zone.loc[zone['on_time_pct'].idxmin(), 'zone']),
        'highest_mean_cost_zone': str(zone.loc[zone['average_cost_inr'].idxmax(), 'zone']),
        'min_on_time_zone_pct': round(float(zone['on_time_pct'].min()),2),
        'max_on_time_zone_pct': round(float(zone['on_time_pct'].max()),2),
        'priority_on_time_pct': round(float(service.loc['Priority','on_time_rate']*100),2),
        'standard_on_time_pct': round(float(service.loc['Standard','on_time_rate']*100),2),
        'rain_on_time_pct': round(float(weather.loc['Rain','on_time_rate']*100),2),
        'clear_on_time_pct': round(float(weather.loc['Clear','on_time_rate']*100),2),
        'high_traffic_on_time_pct': round(float(traffic.loc[traffic['traffic_level']=='High','on_time_pct'].iloc[0]),2),
        'low_traffic_on_time_pct': round(float(traffic.loc[traffic['traffic_level']=='Low','on_time_pct'].iloc[0]),2),
    }
    (out_tables/'summary_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')

    # Visual 1: shipment-volume trend; zero-delivery dates included using resample.
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    ax.plot(daily.index, daily['shipments'], lw=1.25, alpha=.50, label='Daily shipments')
    ax.plot(daily.index, daily['shipments_7day_mean'], lw=2.5, label='7-day moving average')
    ax.set(title='Daily shipment volumes', ylabel='Number of shipments', xlabel='Dispatch date')
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    _save(fig, figs/'01_daily_volume.png')

    # Visual 2: delivery-time distribution.
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.hist(df['actual_delivery_hours'], bins=24, edgecolor='white', linewidth=.5)
    ax.axvline(df['actual_delivery_hours'].mean(), lw=2, ls='--', label='Mean')
    ax.axvline(df['actual_delivery_hours'].median(), lw=2, ls=':', label='Median')
    ax.set(title='Distribution of delivery completion times', xlabel='Actual delivery time (hours)', ylabel='Shipment count')
    ax.legend(frameon=False)
    _save(fig, figs/'02_delivery_time_distribution.png')

    # Visual 3: on-time performance by zone (not overall percent share).
    z = zone.sort_values('on_time_pct')
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    bars = ax.barh(z['zone'], z['on_time_pct'])
    ax.set_xlim(0, 100)
    ax.set(xlabel='On-time delivery rate (%)', title='On-time performance by delivery zone')
    for bar, value in zip(bars, z['on_time_pct']):
        ax.text(min(float(value)+1, 96), bar.get_y()+bar.get_height()/2,
                f'{value:.1f}%', va='center', fontsize=8)
    _save(fig, figs/'03_zone_on_time.png')

    # Visual 4: distance vs cost with best-fit line for descriptive display.
    fig, ax = plt.subplots(figsize=(8.8, 4.5))
    ax.scatter(df['distance_km'], df['transport_cost_inr'], s=14, alpha=.30)
    slope, intercept = np.polyfit(df['distance_km'], df['transport_cost_inr'], 1)
    xs = np.linspace(df['distance_km'].min(), df['distance_km'].max(), 100)
    ax.plot(xs, slope * xs + intercept, lw=2, label=f'Least-squares line (r = {metrics["distance_cost_pearson_r"]:.2f})')
    ax.set(title='Transport cost versus delivery distance', xlabel='Distance (km)', ylabel='Transport cost (INR)')
    ax.legend(frameon=False)
    _save(fig, figs/'04_distance_cost.png')

    # Visual 5: traffic and SLA margin, positive implies late; preserves negative early arrivals.
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    data = [df.loc[df['traffic_level']==key, 'sla_margin_hours'].to_numpy() for key in ['Low','Medium','High']]
    ax.boxplot(data, showfliers=False)
    ax.set_xticks([1, 2, 3], ['Low', 'Medium', 'High'])
    ax.axhline(0, linewidth=1.7, linestyle='--', label='SLA threshold (0 h)')
    ax.set(title='Delivery time relative to SLA by traffic level', xlabel='Traffic level', ylabel='Actual minus promised time (hours)')
    ax.legend(frameon=False)
    _save(fig, figs/'05_traffic_sla_boxplot.png')

    # Visual 6: Pearson correlation heatmap.
    labels = ['Distance', 'Weight', 'Parcels', 'Delivery time', 'Transport cost', 'SLA margin']
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    image = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1, cmap='coolwarm')
    ax.set_xticks(range(len(labels)), labels, rotation=38, ha='right')
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = corr.iat[i,j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    color='white' if abs(v)>.55 else 'black', fontsize=8)
    ax.set(title='Pearson correlation matrix: numeric logistics measures')
    fig.colorbar(image, ax=ax, label='Pearson r', shrink=.8)
    _save(fig, figs/'06_correlation_matrix.png')

    # Visual 7: average cost by zone, avoiding volume confounding of total cost.
    c = zone.sort_values('average_cost_inr')
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.barh(c['zone'], c['average_cost_inr'])
    ax.set(title='Average transport cost per shipment, by zone', xlabel='Mean cost per shipment (INR)')
    _save(fig, figs/'07_zone_mean_cost.png')

    # Visual 8: on-time by service level as complementary service quality measure.
    fig, ax = plt.subplots(figsize=(7.5, 4.1))
    service_pct = service['on_time_rate'].mul(100)
    bars = ax.bar(service_pct.index, service_pct.values, width=.5)
    ax.set_ylim(0, 100)
    ax.set(title='On-time rate by service commitment', ylabel='On-time shipments (%)')
    for bar, value in zip(bars, service_pct.values):
        ax.text(bar.get_x()+bar.get_width()/2, value+1.4, f'{value:.1f}%', ha='center', fontsize=10)
    _save(fig, figs/'08_service_sla.png')
    print(json.dumps(metrics, indent=2))
    return metrics


def _save(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/raw/simulated_shipments.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    df = read_and_validate(args.input)
    write_results(df, args.output_dir)

if __name__ == '__main__':
    main()
