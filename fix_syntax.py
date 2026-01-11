#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix syntax error in realtime_pitch_detector.py"""

filepath = r'd:\project\cubase-tool-py\realtime_pitch_detector.py'

# Read file
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 360 (index 359)
if len(lines) > 359:
    line = lines[359]
    print(f"Original line 360: {repr(line)}")
    
    # Check if this is the problematic line
    if '") except Exception as e:' in line:
        # Split into two lines
        fixed_line1 = line.split(') except')[0] + ')\r\n'
        fixed_line2 = '        except Exception as e:\r\n'
        
        # Replace
        lines[359] = fixed_line1
        lines.insert(360, fixed_line2)
        
        print(f"Fixed line 360: {repr(fixed_line1)}")
        print(f"New line 361: {repr(fixed_line2)}")
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✓ File fixed successfully!")
    else:
        print("Line doesn't match expected pattern. Skipping.")
else:
    print("File doesn't have enough lines!")
