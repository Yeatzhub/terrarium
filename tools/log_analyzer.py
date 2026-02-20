#!/usr/bin/env python3
"""
Log Pattern Analyzer
Analyzes log files for error patterns, frequency, and trends
"""

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def analyze_log_file(log_path):
    """Analyze a log file for patterns"""
    
    log_file = Path(log_path)
    if not log_path.exists():
        print(f"Error: File not found: {log_path}")
        return
    
    # Patterns to search for
    patterns = {
        'errors': r'\b(ERROR|CRITICAL|FATAL)\b',
        'warnings': r'\b(WARNING|WARN)\b',
        'info': r'\b(INFO|DEBUG)\b',
        'exceptions': r'(Exception|Error):\s*(\w+)',
        'timestamps': r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
    }
    
    results = {key: [] for key in patterns.keys()}
    results['unique_exceptions'] = set()
    
    print(f"Analyzing: {log_path}")
    print("=" * 50)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                if pattern_name == 'exceptions':
                    exc_type = match.group(2)
                    results['unique_exceptions'].add(exc_type)
                results[pattern_name].append({
                    'line': line_num,
                    'match': match.group(),
                    'context': line.strip()[:100]
                })
    
    # Print summary
    print(f"\nTotal lines analyzed: {len(lines)}")
    print(f"Errors found: {len(results['errors'])}")
    print(f"Warnings found: {len(results['warnings'])}")
    print(f"Info messages: {len(results['info'])}")
    print(f"Exceptions: {len(results['exceptions'])}")
    print(f"Timestamps: {len(results['timestamps'])}")
    
    # Print unique exceptions
    if results['unique_exceptions']:
        print(f"\nUnique Exception Types:")
        for exc in sorted(results['unique_exceptions']):
            print(f"  - {exc}")
    
    # Most common error patterns
    if results['errors']:
        print(f"\nTop Error Lines:")
        error_lines = Counter(e['line'] for e in results['errors'])
        for line, count in error_lines.most_common(5):
            print(f"  Line {line}: {count} occurrences")
    
    # Sample errors
    if results['errors'][:3]:
        print(f"\nSample Errors:")
        for err in results['errors'][:3]:
            print(f"  Line {err['line']}: {err['context']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python log_analyzer.py <log_file>")
        print("Example: python log_analyzer.py /var/log/syslog")
        sys.exit(1)
    
    log_path = Path(sys.argv[1])
    analyze_log_file(log_path)
