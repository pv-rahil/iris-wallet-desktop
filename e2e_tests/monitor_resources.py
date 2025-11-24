#!/usr/bin/env python3
"""
Resource monitoring utility for E2E tests.
Tracks CPU, memory, disk, and process metrics during test execution.
"""
from __future__ import annotations

import argparse
import csv
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    print('Error: psutil is required. Install with: pip install psutil')
    sys.exit(1)


class ResourceMonitor:
    """Monitor and log system resource usage."""

    def __init__(
        self,
        interval: int = 5,
        output_file: str = 'resource_usage.log',
        summary_file: str = 'resource_summary.txt',
        json_output: str,
    ):
        self.interval = interval
        self.output_file = Path(output_file)
        self.summary_file = Path(summary_file)
        self.json_output = Path(json_output)
        self.running = False
        self.data: list[dict[str, Any]] = []

    def start(self) -> None:
        """Start monitoring resources."""
        print(f"Starting resource monitoring (interval: {self.interval}s)")
        print(f"Output: {self.output_file}")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True
        self._monitor_loop()

    def _signal_handler(self, signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, stopping monitor...")
        self.running = False

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Write CSV header
        with self.output_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'cpu_percent',
                'memory_used_mb',
                'memory_percent',
                'disk_used_gb',
                'disk_percent',
                'load_avg_1m',
                'load_avg_5m',
                'load_avg_15m',
                'processes',
                'threads',
                'swap_used_mb',
                'swap_percent',
            ])

        start_time = datetime.now()

        try:
            while self.running:
                metrics = self._collect_metrics()
                self.data.append(metrics)

                # Append to CSV
                with self.output_file.open('a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        metrics['timestamp'],
                        metrics['cpu_percent'],
                        metrics['memory_used_mb'],
                        metrics['memory_percent'],
                        metrics['disk_used_gb'],
                        metrics['disk_percent'],
                        metrics['load_avg_1m'],
                        metrics['load_avg_5m'],
                        metrics['load_avg_15m'],
                        metrics['processes'],
                        metrics['threads'],
                        metrics['swap_used_mb'],
                        metrics['swap_percent'],
                    ])

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print('\nMonitoring interrupted by user')
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"\nMonitoring stopped. Duration: {duration:.1f}s")
            print(f"Collected {len(self.data)} samples")

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / (1024 * 1024)
        memory_percent = memory.percent

        # Swap usage
        swap = psutil.swap_memory()
        swap_used_mb = swap.used / (1024 * 1024)
        swap_percent = swap.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_percent = disk.percent

        # Load averages
        load_avg = psutil.getloadavg()

        # Process and thread counts
        processes = len(psutil.pids())
        threads = sum(
            p.num_threads()
            for p in psutil.process_iter(['num_threads'])
        )

        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': round(cpu_percent, 2),
            'memory_used_mb': round(memory_used_mb, 2),
            'memory_percent': round(memory_percent, 2),
            'disk_used_gb': round(disk_used_gb, 2),
            'disk_percent': round(disk_percent, 2),
            'load_avg_1m': round(load_avg[0], 2),
            'load_avg_5m': round(load_avg[1], 2),
            'load_avg_15m': round(load_avg[2], 2),
            'processes': processes,
            'threads': threads,
            'swap_used_mb': round(swap_used_mb, 2),
            'swap_percent': round(swap_percent, 2),
        }

    def generate_summary(self) -> None:
        """Generate summary statistics from collected data."""
        if not self.output_file.exists():
            print(f"Error: Log file not found: {self.output_file}")
            return

        # Read data from CSV
        data = []
        with self.output_file.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    k: float(v) if k != 'timestamp' else v
                    for k, v in row.items()
                })

        if not data:
            print('No data to summarize')
            return

        # Calculate statistics
        stats = self._calculate_statistics(data)

        # Write summary to file
        self._write_summary(stats, data)

        # Optionally write JSON output
        if self.json_output:
            self._write_json(stats, data)

        # Display summary
        with self.summary_file.open('r', encoding='utf-8') as f:
            print(f.read())

    def _calculate_statistics(
        self, data: list[dict[str, Any]],
    ) -> dict[str, dict[str, float]]:
        """Calculate min, max, avg statistics for each metric."""
        metrics = [
            'cpu_percent',
            'memory_used_mb',
            'memory_percent',
            'disk_used_gb',
            'disk_percent',
            'load_avg_1m',
            'load_avg_5m',
            'load_avg_15m',
            'processes',
            'threads',
            'swap_used_mb',
            'swap_percent',
        ]

        stats = {}
        for metric in metrics:
            values = [d[metric] for d in data]
            stats[metric] = {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
            }

        return stats

    def _write_summary(
        self, stats: dict[str, dict[str, float]], data: list[dict[str, Any]],
    ) -> None:
        """Write summary to text file."""
        with self.summary_file.open('w', encoding='utf-8') as f:
            f.write('Resource Usage Summary\n')
            f.write('=' * 60 + '\n\n')

            f.write('Monitoring Period:\n')
            f.write(f"  Start: {data[0]['timestamp']}\n")
            f.write(f"  End:   {data[-1]['timestamp']}\n")
            f.write(f"  Samples: {len(data)}\n\n")

            f.write('CPU Usage (%):\n')
            f.write(f"  Average: {stats['cpu_percent']['avg']:.2f}%\n")
            f.write(f"  Maximum: {stats['cpu_percent']['max']:.2f}%\n")
            f.write(f"  Minimum: {stats['cpu_percent']['min']:.2f}%\n\n")

            f.write('Memory Usage (MB):\n')
            f.write(f"  Average: {stats['memory_used_mb']['avg']:.2f} MB\n")
            f.write(f"  Maximum: {stats['memory_used_mb']['max']:.2f} MB\n")
            f.write(f"  Minimum: {stats['memory_used_mb']['min']:.2f} MB\n\n")

            f.write('Memory Usage (%):\n')
            f.write(f"  Average: {stats['memory_percent']['avg']:.2f}%\n")
            f.write(f"  Maximum: {stats['memory_percent']['max']:.2f}%\n")
            f.write(f"  Minimum: {stats['memory_percent']['min']:.2f}%\n\n")

            f.write('Swap Usage (MB):\n')
            f.write(f"  Average: {stats['swap_used_mb']['avg']:.2f} MB\n")
            f.write(f"  Maximum: {stats['swap_used_mb']['max']:.2f} MB\n")
            f.write(f"  Minimum: {stats['swap_used_mb']['min']:.2f} MB\n\n")

            f.write('Disk Usage (GB):\n')
            f.write(f"  Average: {stats['disk_used_gb']['avg']:.2f} GB\n")
            f.write(f"  Maximum: {stats['disk_used_gb']['max']:.2f} GB\n")
            f.write(f"  Minimum: {stats['disk_used_gb']['min']:.2f} GB\n\n")

            f.write('Load Average (1m):\n')
            f.write(f"  Average: {stats['load_avg_1m']['avg']:.2f}\n")
            f.write(f"  Maximum: {stats['load_avg_1m']['max']:.2f}\n")
            f.write(f"  Minimum: {stats['load_avg_1m']['min']:.2f}\n\n")

            f.write('Process Count:\n')
            f.write(f"  Average: {stats['processes']['avg']:.0f}\n")
            f.write(f"  Maximum: {stats['processes']['max']:.0f}\n")
            f.write(f"  Minimum: {stats['processes']['min']:.0f}\n\n")

            f.write('Thread Count:\n')
            f.write(f"  Average: {stats['threads']['avg']:.0f}\n")
            f.write(f"  Maximum: {stats['threads']['max']:.0f}\n")
            f.write(f"  Minimum: {stats['threads']['min']:.0f}\n")

    def _write_json(
        self, stats: dict[str, dict[str, float]], data: list[dict[str, Any]],
    ) -> None:
        """Write summary and data to JSON file."""
        output = {
            'summary': stats,
            'monitoring_period': {
                'start': data[0]['timestamp'],
                'end': data[-1]['timestamp'],
                'samples': len(data),
            },
            'data': data,
        }

        with self.json_output.open('w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print(f"JSON output written to: {self.json_output}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Monitor system resource usage during test execution',
    )
    subparsers = parser.add_subparsers(
        dest='command', help='Command to execute',
    )

    # Start command
    start_parser = subparsers.add_parser('start', help='Start monitoring')
    start_parser.add_argument(
        '-i',
        '--interval',
        type=int,
        default=5,
        help='Monitoring interval in seconds (default: 5)',
    )
    start_parser.add_argument(
        '-o',
        '--output',
        default='resource_usage.log',
        help='Output log file (default: resource_usage.log)',
    )
    start_parser.add_argument(
        '-s',
        '--summary',
        default='resource_summary.txt',
        help='Summary file (default: resource_summary.txt)',
    )
    start_parser.add_argument(
        '-j', '--json', help='JSON output file (optional)',
    )

    # Summary command
    summary_parser = subparsers.add_parser(
        'summary', help='Generate summary from log file',
    )
    summary_parser.add_argument(
        '-o',
        '--output',
        default='resource_usage.log',
        help='Input log file (default: resource_usage.log)',
    )
    summary_parser.add_argument(
        '-s',
        '--summary',
        default='resource_summary.txt',
        help='Summary file (default: resource_summary.txt)',
    )
    summary_parser.add_argument(
        '-j', '--json', help='JSON output file (optional)',
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'start':
        monitor = ResourceMonitor(
            interval=args.interval,
            output_file=args.output,
            summary_file=args.summary,
            json_output=args.json,
        )
        monitor.start()
    elif args.command == 'summary':
        monitor = ResourceMonitor(
            output_file=args.output,
            summary_file=args.summary,
            json_output=args.json,
        )
        monitor.generate_summary()


if __name__ == '__main__':
    main()
