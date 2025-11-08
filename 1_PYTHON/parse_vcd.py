#!/usr/bin/env python3
"""
Parse VCD file to trace critical signals around first output.
Focus on: pixel_valid, col_addr, window formation, BRAM data
"""
import re

def parse_vcd_header(vcd_file):
    """Parse VCD header to get signal IDs"""
    signals = {}
    with open(vcd_file, 'r') as f:
        in_scope = False
        current_scope = []
        
        for line in f:
            line = line.strip()
            
            if line.startswith('$scope'):
                parts = line.split()
                if len(parts) >= 3:
                    current_scope.append(parts[2])
            elif line.startswith('$upscope'):
                if current_scope:
                    current_scope.pop()
            elif line.startswith('$var'):
                # $var wire 1 ! pixel_valid $end
                parts = line.split()
                if len(parts) >= 5:
                    var_type = parts[1]
                    var_width = parts[2]
                    var_id = parts[3]
                    var_name = parts[4]
                    scope_path = '.'.join(current_scope)
                    full_name = f"{scope_path}.{var_name}" if scope_path else var_name
                    signals[var_id] = {
                        'name': var_name,
                        'full_name': full_name,
                        'width': int(var_width),
                        'type': var_type
                    }
            elif line.startswith('$enddefinitions'):
                break
    
    return signals

def trace_signals_around_output(vcd_file, target_time_start=8600000, target_time_end=8900000):
    """Trace signals around first output"""
    
    # Parse header
    signals = parse_vcd_header(vcd_file)
    
    # Find signal IDs we care about
    target_signals = [
        'pixel_valid', 'pixel_valid_d1', 'pixel_valid_d2',
        'col_addr', 'col_addr_d1', 'col_addr_d2',
        'row_count', 'row_count_d1', 'row_count_d2',
        'window_valid', 'pixel_out',
        'line2_q', 'line1_q', 'pixel_in_d2',
        'top_row[0]', 'top_row[1]', 'top_row[2]',
        'mid_row[0]', 'mid_row[1]', 'mid_row[2]',
        'bot_row[0]', 'bot_row[1]', 'bot_row[2]',
        'prefill_active'
    ]
    
    # Build reverse lookup
    id_to_name = {}
    for sig_id, info in signals.items():
        for target in target_signals:
            if target in info['name']:
                id_to_name[sig_id] = info['name']
                break
    
    print(f"Found {len(id_to_name)} signals to trace")
    print("Signal IDs:", id_to_name)
    
    # Parse value changes
    current_time = 0
    signal_values = {name: 'x' for name in id_to_name.values()}
    
    print(f"\n=== Tracing from time {target_time_start} to {target_time_end} ===\n")
    
    with open(vcd_file, 'r') as f:
        in_data = False
        
        for line in f:
            line = line.strip()
            
            if line.startswith('$enddefinitions'):
                in_data = True
                continue
            
            if not in_data:
                continue
            
            # Time change
            if line.startswith('#'):
                current_time = int(line[1:])
                
                # Print state at interesting times
                if target_time_start <= current_time <= target_time_end:
                    if current_time % 40000 == 0:  # Every clock cycle (40ns period)
                        print(f"\n--- Time {current_time} (cycle {current_time//40000}) ---")
                        
                        # Print key signals
                        print(f"  pixel_valid={signal_values.get('pixel_valid', '?')}, "
                              f"pixel_valid_d1={signal_values.get('pixel_valid_d1', '?')}, "
                              f"pixel_valid_d2={signal_values.get('pixel_valid_d2', '?')}")
                        print(f"  col_addr={signal_values.get('col_addr', '?')}, "
                              f"col_addr_d1={signal_values.get('col_addr_d1', '?')}, "
                              f"col_addr_d2={signal_values.get('col_addr_d2', '?')}")
                        print(f"  window_valid={signal_values.get('window_valid', '?')}, "
                              f"pixel_out={signal_values.get('pixel_out', '?')}")
                        
                        # Print window
                        top = [signal_values.get(f'top_row[{i}]', '?') for i in range(3)]
                        mid = [signal_values.get(f'mid_row[{i}]', '?') for i in range(3)]
                        bot = [signal_values.get(f'bot_row[{i}]', '?') for i in range(3)]
                        print(f"  Window: {top} / {mid} / {bot}")
                        print(f"  BRAM: line2_q={signal_values.get('line2_q', '?')}, "
                              f"line1_q={signal_values.get('line1_q', '?')}, "
                              f"pixel_in_d2={signal_values.get('pixel_in_d2', '?')}")
                
                continue
            
            # Value change
            if line and line[0] in '01xXzZ':
                # 1-bit value
                value = line[0]
                sig_id = line[1:]
                if sig_id in id_to_name:
                    signal_values[id_to_name[sig_id]] = value
            elif line and line[0] == 'b':
                # Multi-bit value: b0110 !
                parts = line.split()
                if len(parts) == 2:
                    value_bin = parts[0][1:]  # Remove 'b'
                    sig_id = parts[1]
                    if sig_id in id_to_name:
                        # Convert to hex
                        try:
                            value_int = int(value_bin, 2) if 'x' not in value_bin.lower() else 0
                            signal_values[id_to_name[sig_id]] = f"0x{value_int:x}"
                        except:
                            signal_values[id_to_name[sig_id]] = value_bin

if __name__ == '__main__':
    import sys
    vcd_file = '../sim/sobel_wave.vcd' if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"Parsing VCD file: {vcd_file}")
    trace_signals_around_output(vcd_file)
