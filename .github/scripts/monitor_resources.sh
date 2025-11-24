#!/usr/bin/env bash

# Resource monitoring script for CI/CD runners
# Continuously monitors and logs system resource usage

set -euo pipefail

# Configuration
INTERVAL=${MONITOR_INTERVAL:-5}  # Monitoring interval in seconds
OUTPUT_FILE=${MONITOR_OUTPUT:-"resource_usage.log"}
SUMMARY_FILE=${MONITOR_SUMMARY:-"resource_summary.txt"}
PID_FILE="/tmp/resource_monitor.pid"

# Initialize log file with headers
init_log() {
    echo "timestamp,cpu_percent,memory_used_mb,memory_percent,disk_used_gb,disk_percent,load_avg_1m,load_avg_5m,load_avg_15m,processes" > "$OUTPUT_FILE"
    echo "Resource monitoring started at $(date)" > "$SUMMARY_FILE"
    echo "Monitoring interval: ${INTERVAL}s" >> "$SUMMARY_FILE"
    echo "----------------------------------------" >> "$SUMMARY_FILE"
}

# Get CPU usage percentage
get_cpu_usage() {
    # Use top to get CPU usage (100 - idle)
    top -bn2 -d 0.5 | grep "Cpu(s)" | tail -n1 | awk '{print 100 - $8}'
}

# Get memory usage
get_memory_usage() {
    free -m | awk 'NR==2{printf "%.2f,%.2f", $3, $3*100/$2}'
}

# Get disk usage
get_disk_usage() {
    df -BG / | awk 'NR==2{gsub(/G/,"",$3); gsub(/%/,"",$5); printf "%s,%s", $3, $5}'
}

# Get load averages
get_load_avg() {
    uptime | awk -F'load average:' '{print $2}' | awk '{gsub(/ /,""); print $1","$2","$3}'
}

# Get number of processes
get_process_count() {
    # Subtract 1 for the header line
    echo $(($(ps aux | wc -l) - 1))
}

# Monitor resources continuously
monitor() {
    init_log

    echo $$ > "$PID_FILE"

    while true; do
        timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        cpu=$(get_cpu_usage)
        memory=$(get_memory_usage)
        disk=$(get_disk_usage)
        load=$(get_load_avg)
        processes=$(get_process_count)

        echo "$timestamp,$cpu,$memory,$disk,$load,$processes" >> "$OUTPUT_FILE"

        sleep "$INTERVAL"
    done
}

# Generate summary statistics
generate_summary() {
    if [[ ! -f "$OUTPUT_FILE" ]]; then
        echo "No resource log file found at $OUTPUT_FILE"
        return 1
    fi

    echo "" >> "$SUMMARY_FILE"
    echo "Resource Usage Summary" >> "$SUMMARY_FILE"
    echo "======================" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # CPU statistics
    echo "CPU Usage (%):" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$2; if(NR==2 || $2>max) max=$2; if(NR==2 || $2<min) min=$2; count++}
                END {printf "  Average: %.2f%%\n  Maximum: %.2f%%\n  Minimum: %.2f%%\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Memory statistics
    echo "Memory Usage (MB):" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$3; if(NR==2 || $3>max) max=$3; if(NR==2 || $3<min) min=$3; count++}
                END {printf "  Average: %.2f MB\n  Maximum: %.2f MB\n  Minimum: %.2f MB\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    echo "Memory Usage (%):" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$4; if(NR==2 || $4>max) max=$4; if(NR==2 || $4<min) min=$4; count++}
                END {printf "  Average: %.2f%%\n  Maximum: %.2f%%\n  Minimum: %.2f%%\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Disk statistics
    echo "Disk Usage (GB):" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$5; if(NR==2 || $5>max) max=$5; if(NR==2 || $5<min) min=$5; count++}
                END {printf "  Average: %.2f GB\n  Maximum: %.2f GB\n  Minimum: %.2f GB\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Load average statistics
    echo "Load Average (1m):" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$7; if(NR==2 || $7>max) max=$7; if(NR==2 || $7<min) min=$7; count++}
                END {printf "  Average: %.2f\n  Maximum: %.2f\n  Minimum: %.2f\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Process count statistics
    echo "Process Count:" >> "$SUMMARY_FILE"
    awk -F',' 'NR>1 {sum+=$10; if(NR==2 || $10>max) max=$10; if(NR==2 || $10<min) min=$10; count++}
                END {printf "  Average: %.0f\n  Maximum: %d\n  Minimum: %d\n", sum/count, max, min}' \
                "$OUTPUT_FILE" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Total monitoring duration
    start_time=$(awk -F',' 'NR==2 {print $1}' "$OUTPUT_FILE")
    end_time=$(awk -F',' 'END {print $1}' "$OUTPUT_FILE")
    echo "Monitoring Period:" >> "$SUMMARY_FILE"
    echo "  Start: $start_time" >> "$SUMMARY_FILE"
    echo "  End: $end_time" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"

    # Display summary
    cat "$SUMMARY_FILE"
}

# Stop monitoring
stop_monitor() {
    if [[ -f "$PID_FILE" ]]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "Resource monitoring stopped (PID: $pid)"
        fi
        rm -f "$PID_FILE"
    else
        echo "No monitoring process found"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        echo "Starting resource monitoring..."
        monitor &
        echo "Resource monitoring started in background (PID: $!)"
        ;;
    stop)
        echo "Stopping resource monitoring..."
        stop_monitor
        ;;
    summary)
        echo "Generating resource usage summary..."
        generate_summary
        ;;
    *)
        echo "Usage: $0 {start|stop|summary}"
        echo ""
        echo "Commands:"
        echo "  start   - Start resource monitoring in background"
        echo "  stop    - Stop resource monitoring"
        echo "  summary - Generate and display summary statistics"
        echo ""
        echo "Environment variables:"
        echo "  MONITOR_INTERVAL - Monitoring interval in seconds (default: 5)"
        echo "  MONITOR_OUTPUT   - Output log file (default: resource_usage.log)"
        echo "  MONITOR_SUMMARY  - Summary file (default: resource_summary.txt)"
        exit 1
        ;;
esac
