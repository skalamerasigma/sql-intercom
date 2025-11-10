"""
Visualize MRR vs Chat Volume correlation.

Creates scatter plots and time series visualizations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
	import matplotlib.pyplot as plt
	import matplotlib.dates as mdates
	from datetime import datetime
	MATPLOTLIB_AVAILABLE = True
except ImportError:
	MATPLOTLIB_AVAILABLE = False
	print("Warning: matplotlib not available. Install with: pip install matplotlib")
	print("Skipping visualization generation.")


def load_analysis_data(json_path: str) -> dict:
	"""Load analysis results from JSON file."""
	with open(json_path, 'r') as f:
		return json.load(f)


def create_scatter_plot(analysis: dict, output_path: str):
	"""Create scatter plot of MRR vs Conversations."""
	if not MATPLOTLIB_AVAILABLE:
		return
	
	monthly_data = analysis['monthly_data']
	
	mrr_values = [d['total_mrr'] for d in monthly_data]
	conversation_values = [d['total_conversations'] for d in monthly_data]
	
	fig, ax = plt.subplots(figsize=(12, 8))
	
	# Create scatter plot
	ax.scatter(mrr_values, conversation_values, alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
	
	# Add trend line
	import numpy as np
	z = np.polyfit(mrr_values, conversation_values, 1)
	p = np.poly1d(z)
	ax.plot(mrr_values, p(mrr_values), "r--", alpha=0.8, linewidth=2, label=f'Trend line (r={analysis["correlations"]["mrr_vs_total_conversations"]["coefficient"]:.3f})')
	
	ax.set_xlabel('Monthly Recurring Revenue (MRR) - $', fontsize=12, fontweight='bold')
	ax.set_ylabel('Total Monthly Conversations', fontsize=12, fontweight='bold')
	ax.set_title('MRR vs Chat Volume Correlation\n(Strong Positive Correlation: r=0.805)', 
	             fontsize=14, fontweight='bold', pad=20)
	ax.grid(True, alpha=0.3)
	ax.legend()
	
	# Format x-axis as currency
	ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
	
	plt.tight_layout()
	plt.savefig(output_path, dpi=300, bbox_inches='tight')
	print(f"Scatter plot saved to: {output_path}")
	plt.close()


def create_time_series_plot(analysis: dict, output_path: str):
	"""Create time series plot showing MRR and Conversations over time."""
	if not MATPLOTLIB_AVAILABLE:
		return
	
	monthly_data = analysis['monthly_data']
	
	dates = [datetime.strptime(d['month'], '%Y-%m') for d in monthly_data]
	mrr_values = [d['total_mrr'] for d in monthly_data]
	conversation_values = [d['total_conversations'] for d in monthly_data]
	
	fig, ax1 = plt.subplots(figsize=(14, 8))
	
	# Plot MRR on left y-axis
	color = 'tab:blue'
	ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
	ax1.set_ylabel('Monthly Recurring Revenue (MRR) - $', color=color, fontsize=12, fontweight='bold')
	line1 = ax1.plot(dates, mrr_values, color=color, linewidth=2, label='MRR', marker='o', markersize=4)
	ax1.tick_params(axis='y', labelcolor=color)
	ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
	ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
	plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
	ax1.grid(True, alpha=0.3)
	ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
	
	# Plot Conversations on right y-axis
	ax2 = ax1.twinx()
	color = 'tab:red'
	ax2.set_ylabel('Total Monthly Conversations', color=color, fontsize=12, fontweight='bold')
	line2 = ax2.plot(dates, conversation_values, color=color, linewidth=2, label='Conversations', marker='s', markersize=4)
	ax2.tick_params(axis='y', labelcolor=color)
	
	# Add title
	corr_coef = analysis['correlations']['mrr_vs_total_conversations']['coefficient']
	ax1.set_title(f'MRR and Chat Volume Over Time\n(Correlation: r={corr_coef:.3f})', 
	              fontsize=14, fontweight='bold', pad=20)
	
	# Combine legends
	lines = line1 + line2
	labels = [l.get_label() for l in lines]
	ax1.legend(lines, labels, loc='upper left')
	
	plt.tight_layout()
	plt.savefig(output_path, dpi=300, bbox_inches='tight')
	print(f"Time series plot saved to: {output_path}")
	plt.close()


def create_daily_average_plot(analysis: dict, output_path: str):
	"""Create scatter plot of MRR vs Average Daily Conversations."""
	if not MATPLOTLIB_AVAILABLE:
		return
	
	monthly_data = analysis['monthly_data']
	
	mrr_values = [d['total_mrr'] for d in monthly_data]
	daily_avg_values = [d['avg_daily_conversations'] for d in monthly_data]
	
	fig, ax = plt.subplots(figsize=(12, 8))
	
	# Create scatter plot
	ax.scatter(mrr_values, daily_avg_values, alpha=0.6, s=100, edgecolors='black', linewidth=0.5, color='green')
	
	# Add trend line
	import numpy as np
	z = np.polyfit(mrr_values, daily_avg_values, 1)
	p = np.poly1d(z)
	corr_coef = analysis['correlations']['mrr_vs_avg_daily_conversations']['coefficient']
	ax.plot(mrr_values, p(mrr_values), "r--", alpha=0.8, linewidth=2, 
	        label=f'Trend line (r={corr_coef:.3f})')
	
	ax.set_xlabel('Monthly Recurring Revenue (MRR) - $', fontsize=12, fontweight='bold')
	ax.set_ylabel('Average Daily Conversations', fontsize=12, fontweight='bold')
	ax.set_title('MRR vs Average Daily Chat Volume\n(Very Strong Positive Correlation: r=0.868)', 
	             fontsize=14, fontweight='bold', pad=20)
	ax.grid(True, alpha=0.3)
	ax.legend()
	
	# Format x-axis as currency
	ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
	
	plt.tight_layout()
	plt.savefig(output_path, dpi=300, bbox_inches='tight')
	print(f"Daily average plot saved to: {output_path}")
	plt.close()


def main():
	"""Main execution function."""
	json_path = '/Users/stephen.skalamera/Documents/Projects/Intercom App/mrr_chat_correlation_analysis.json'
	output_dir = Path('/Users/stephen.skalamera/Documents/Projects/Intercom App')
	
	if not Path(json_path).exists():
		print(f"Error: Analysis file not found: {json_path}")
		print("Please run analyze_mrr_chat_correlation.py first.")
		sys.exit(1)
	
	analysis = load_analysis_data(json_path)
	
	if not MATPLOTLIB_AVAILABLE:
		print("\nVisualizations skipped - matplotlib not installed.")
		print("To generate visualizations, install matplotlib:")
		print("  pip install matplotlib numpy")
		return
	
	print("Generating visualizations...")
	
	# Create scatter plot
	scatter_path = output_dir / 'mrr_chat_scatter.png'
	create_scatter_plot(analysis, str(scatter_path))
	
	# Create time series plot
	timeseries_path = output_dir / 'mrr_chat_timeseries.png'
	create_time_series_plot(analysis, str(timeseries_path))
	
	# Create daily average plot
	daily_path = output_dir / 'mrr_chat_daily_avg.png'
	create_daily_average_plot(analysis, str(daily_path))
	
	print("\nAll visualizations generated successfully!")


if __name__ == '__main__':
	main()

