#!/usr/bin/env python3
import argparse
import json
import os

def split_json_file(input_file, output_dir, max_file_size=50 * 1024 * 1024):  # 50 MB in bytes
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize variables for splitting
    current_chunk_size = 0
    file_count = 1

    # Open the first output file
    output_file = os.path.join(output_dir, f'split_{file_count}.json')
    outfile = open(output_file, 'w')

    # Read the file line by line (for multi-object JSON files, or NDJSON)
    with open(input_file, 'r') as infile:
        for line in infile:
            try:
                # Parse each line as JSON to ensure it's valid
                record = json.loads(line)
            except json.JSONDecodeError:
                # Skip invalid lines
                print(f"Skipping invalid JSON line: {line}")
                continue

            # Get the size of the record in bytes
            record_size = len(json.dumps(record).encode('utf-8'))

            # If adding this record exceeds the max file size, close current file and open a new one
            if current_chunk_size + record_size > max_file_size:
                outfile.close()  # Close the current file
                file_count += 1
                output_file = os.path.join(output_dir, f'split_{file_count}.json')
                outfile = open(output_file, 'w')  # Open a new file
                current_chunk_size = 0  # Reset the chunk size

            # Write the record as NDJSON (newline-delimited)
            outfile.write(json.dumps(record) + '\n')

            # Update the current chunk size
            current_chunk_size += record_size

    # Close the last output file
    outfile.close()

    print(f'Successfully split into {file_count} NDJSON files.')

# Argument parsing to mimic your required format
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split a large JSON file into smaller NDJSON files.')
    parser.add_argument('-f', '--force', help='Force overwrite existing output files (not used in this script)', action='store_true')
    parser.add_argument('-r', '--read', dest='input_file', required=True, help='Path to the large JSON file to split.')
    parser.add_argument('-w', '--write', dest='output_dir', required=True, help='Directory to write the smaller NDJSON files to.')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.isfile(args.input_file):
        print(f"Error: The input file '{args.input_file}' does not exist.")
        exit(1)

    # Call the function to split the JSON file
    split_json_file(args.input_file, args.output_dir)
