"""
Visualization functions for support headcount forecasting.

Creates plots and charts for analysis and forecast visualization.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional
from pathlib import Path

try:
	import matplotlib
	matplotlib.use('Agg')  # Use non-interactive backend
	import matplotlib.pyplot as plt
	import matplotlib.dates as mdates
	from matplotlib.figure import Figure
	MATPLOTLIB_AVAILABLE = True
except ImportError:
	MATPLOTLIB_AVAILABLE = False
	Figure = None


def plot_historical_volume(
	daily_data: Dict[str, Dict],
	output_path: Optional[str] = None,
	title: str = "Historical Chat Volume"
) -> Optional[Figure]:
	"""
	Plot historical daily chat volume over time.
	
	Returns matplotlib Figure if matplotlib is available, None otherwise.
	"""
	if not MATPLOTLIB_AVAILABLE:
		print("Warning: matplotlib not available, skipping plot")
		return None
	
	# Prepare data
	dates = []
	volumes = []
	
	sorted_keys = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	for key in sorted_keys:
		data = daily_data[key]
		if data['date']:
			dates.append(data['date'])
			volumes.append(data['total_chats'])
	
	if not dates:
		return None
	
	# Create plot
	fig, ax = plt.subplots(figsize=(12, 6))
	ax.plot(dates, volumes, linewidth=1, alpha=0.7, label='Daily Volume')
	
	# Add moving average
	if len(volumes) >= 7:
		import statistics
		window = 7
		ma_values = []
		for i in range(len(volumes)):
			start = max(0, i - window // 2)
			end = min(len(volumes), i + window // 2 + 1)
			ma_values.append(statistics.mean(volumes[start:end]))
		ax.plot(dates, ma_values, linewidth=2, label=f'{window}-Day Moving Average', color='orange')
	
	ax.set_xlabel('Date')
	ax.set_ylabel('Daily Chat Volume')
	ax.set_title(title)
	ax.legend()
	ax.grid(True, alpha=0.3)
	
	# Format x-axis dates
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	ax.xaxis.set_major_locator(mdates.MonthLocator())
	plt.xticks(rotation=45)
	plt.tight_layout()
	
	if output_path:
		fig.savefig(output_path, dpi=150, bbox_inches='tight')
		print(f"Saved plot to {output_path}")
	
	return fig


def plot_forecast(
	historical_data: Dict[str, Dict],
	forecasts: List[Dict],
	output_path: Optional[str] = None,
	title: str = "Chat Volume Forecast"
) -> Optional[Figure]:
	"""
	Plot historical data with forecast overlay.
	
	Returns matplotlib Figure if matplotlib is available, None otherwise.
	"""
	if not MATPLOTLIB_AVAILABLE:
		print("Warning: matplotlib not available, skipping plot")
		return None
	
	# Prepare historical data
	hist_dates = []
	hist_volumes = []
	
	sorted_keys = sorted([k for k in historical_data.keys() if historical_data[k]['date']])
	for key in sorted_keys:
		data = historical_data[key]
		if data['date']:
			hist_dates.append(data['date'])
			hist_volumes.append(data['total_chats'])
	
	# Prepare forecast data
	forecast_dates = [f['date'] for f in forecasts]
	forecast_volumes = [f['projected_chats'] for f in forecasts]
	forecast_lower = [f['confidence_lower'] for f in forecasts]
	forecast_upper = [f['confidence_upper'] for f in forecasts]
	
	if not hist_dates and not forecast_dates:
		return None
	
	# Create plot
	fig, ax = plt.subplots(figsize=(14, 7))
	
	# Plot historical
	if hist_dates:
		ax.plot(hist_dates, hist_volumes, linewidth=1, alpha=0.6, label='Historical', color='blue')
	
	# Plot forecast
	if forecast_dates:
		ax.plot(forecast_dates, forecast_volumes, linewidth=2, label='Forecast', color='green')
		ax.fill_between(
			forecast_dates,
			forecast_lower,
			forecast_upper,
			alpha=0.2,
			label='80% Confidence Interval',
			color='green'
		)
		
		# Highlight holiday periods
		holiday_dates = [f['date'] for f in forecasts if f['is_holiday']]
		holiday_volumes = [f['projected_chats'] for f in forecasts if f['is_holiday']]
		if holiday_dates:
			ax.scatter(holiday_dates, holiday_volumes, color='red', s=50, alpha=0.7, label='Holiday Periods', zorder=5)
	
	ax.set_xlabel('Date')
	ax.set_ylabel('Daily Chat Volume')
	ax.set_title(title)
	ax.legend()
	ax.grid(True, alpha=0.3)
	
	# Format x-axis dates
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	ax.xaxis.set_major_locator(mdates.MonthLocator())
	plt.xticks(rotation=45)
	plt.tight_layout()
	
	if output_path:
		fig.savefig(output_path, dpi=150, bbox_inches='tight')
		print(f"Saved plot to {output_path}")
	
	return fig


def plot_headcount_forecast(
	forecasts: List[Dict],
	output_path: Optional[str] = None,
	title: str = "Required Headcount Forecast"
) -> Optional[Figure]:
	"""
	Plot required headcount over forecast period.
	
	Returns matplotlib Figure if matplotlib is available, None otherwise.
	"""
	if not MATPLOTLIB_AVAILABLE:
		print("Warning: matplotlib not available, skipping plot")
		return None
	
	forecast_dates = [f['date'] for f in forecasts]
	headcounts = [f['required_headcount'] for f in forecasts]
	
	if not forecast_dates:
		return None
	
	# Create plot
	fig, ax = plt.subplots(figsize=(14, 7))
	ax.plot(forecast_dates, headcounts, linewidth=2, marker='o', markersize=4, label='Required Headcount', color='purple')
	
	# Highlight holiday periods
	holiday_dates = [f['date'] for f in forecasts if f['is_holiday']]
	holiday_headcounts = [f['required_headcount'] for f in forecasts if f['is_holiday']]
	if holiday_dates:
		ax.scatter(holiday_dates, holiday_headcounts, color='red', s=100, alpha=0.7, label='Holiday Periods', zorder=5)
	
	# Add target line for average
	avg_headcount = sum(headcounts) / len(headcounts)
	ax.axhline(y=avg_headcount, color='gray', linestyle='--', alpha=0.5, label=f'Average: {avg_headcount:.1f}')
	
	ax.set_xlabel('Date')
	ax.set_ylabel('Required TSE Headcount')
	ax.set_title(title)
	ax.legend()
	ax.grid(True, alpha=0.3)
	
	# Format x-axis dates
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	ax.xaxis.set_major_locator(mdates.MonthLocator())
	plt.xticks(rotation=45)
	plt.tight_layout()
	
	if output_path:
		fig.savefig(output_path, dpi=150, bbox_inches='tight')
		print(f"Saved plot to {output_path}")
	
	return fig


def plot_holiday_comparison(
	daily_data: Dict[str, Dict],
	holiday_impacts: Dict[str, Dict],
	output_path: Optional[str] = None,
	title: str = "Holiday Impact Comparison"
) -> Optional[Figure]:
	"""
	Plot comparison of holiday vs baseline volumes.
	
	Returns matplotlib Figure if matplotlib is available, None otherwise.
	"""
	if not MATPLOTLIB_AVAILABLE:
		print("Warning: matplotlib not available, skipping plot")
		return None
	
	# Prepare data
	holiday_types = []
	multipliers = []
	sample_sizes = []
	
	for holiday_type, impact in holiday_impacts.items():
		if impact['sample_size'] > 0:
			holiday_types.append(holiday_type.replace('_', ' ').title())
			multipliers.append(impact['volume_multiplier'])
			sample_sizes.append(impact['sample_size'])
	
	if not holiday_types:
		return None
	
	# Create plot
	fig, ax = plt.subplots(figsize=(10, 6))
	bars = ax.bar(holiday_types, multipliers, alpha=0.7, color='steelblue')
	
	# Add reference line at 1.0
	ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Baseline (1.0x)')
	
	# Add value labels on bars
	for i, (bar, mult) in enumerate(zip(bars, multipliers)):
		height = bar.get_height()
		ax.text(bar.get_x() + bar.get_width()/2., height,
		        f'{mult:.2f}x\n(n={sample_sizes[i]})',
		        ha='center', va='bottom', fontsize=9)
	
	ax.set_ylabel('Volume Multiplier')
	ax.set_title(title)
	ax.legend()
	ax.grid(True, alpha=0.3, axis='y')
	plt.xticks(rotation=45, ha='right')
	plt.tight_layout()
	
	if output_path:
		fig.savefig(output_path, dpi=150, bbox_inches='tight')
		print(f"Saved plot to {output_path}")
	
	return fig


def plot_csat_trends(
	daily_data: Dict[str, Dict],
	output_path: Optional[str] = None,
	title: str = "CSAT Trends Over Time"
) -> Optional[Figure]:
	"""
	Plot CSAT trends over time.
	
	Returns matplotlib Figure if matplotlib is available, None otherwise.
	"""
	if not MATPLOTLIB_AVAILABLE:
		print("Warning: matplotlib not available, skipping plot")
		return None
	
	# Prepare data
	dates = []
	csats = []
	
	sorted_keys = sorted([k for k in daily_data.keys() if daily_data[k]['date']])
	for key in sorted_keys:
		data = daily_data[key]
		if data['date'] and data['avg_csat'] is not None:
			dates.append(data['date'])
			csats.append(data['avg_csat'])
	
	if not dates:
		return None
	
	# Create plot
	fig, ax = plt.subplots(figsize=(12, 6))
	ax.plot(dates, csats, linewidth=1, alpha=0.7, marker='o', markersize=3, label='Daily CSAT')
	
	# Add target line
	ax.axhline(y=4.7, color='green', linestyle='--', alpha=0.7, label='Target (4.7)')
	
	# Add moving average
	if len(csats) >= 7:
		import statistics
		window = 7
		ma_values = []
		for i in range(len(csats)):
			start = max(0, i - window // 2)
			end = min(len(csats), i + window // 2 + 1)
			ma_values.append(statistics.mean(csats[start:end]))
		ax.plot(dates, ma_values, linewidth=2, label=f'{window}-Day Moving Average', color='orange')
	
	ax.set_xlabel('Date')
	ax.set_ylabel('CSAT Rating')
	ax.set_title(title)
	ax.set_ylim([0, 5])
	ax.legend()
	ax.grid(True, alpha=0.3)
	
	# Format x-axis dates
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	ax.xaxis.set_major_locator(mdates.MonthLocator())
	plt.xticks(rotation=45)
	plt.tight_layout()
	
	if output_path:
		fig.savefig(output_path, dpi=150, bbox_inches='tight')
		print(f"Saved plot to {output_path}")
	
	return fig

