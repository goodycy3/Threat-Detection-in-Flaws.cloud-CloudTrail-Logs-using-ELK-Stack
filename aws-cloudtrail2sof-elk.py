#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script will recursively read a file or directory tree of JSON AWS Cloudtrail logs and output in a format that SOF-ELK® can read.  Both gzipped and native JSON are supported.

import argparse
import gzip
import json
import os
import sys

default_destdir = '/logstash/aws/'

def process_cloudtrail_file(infile, outfh):
    # Determine if this is a gzip file
    try:
        input_file = gzip.open(infile, 'r')
        input_file.read()  # Try reading gzip content
        is_gzip = True
        input_file.seek(0)
    except OSError:
        # Not a gzip file, open as binary
        is_gzip = False
        input_file = open(infile, 'rb')

    try:
        if is_gzip:
            # Load directly for gzip
            rawjson = json.load(input_file)
        else:
            # Decode binary content with error handling for non-gzip files
            file_content = input_file.read()
            try:
                # Attempt UTF-8 decoding first
                rawjson = json.loads(file_content.decode('utf-8'))
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                rawjson = json.loads(file_content.decode('latin-1'))
    
    except json.decoder.JSONDecodeError:
        sys.stderr.write(f'- ERROR: Could not process JSON from {infile}. Skipping file.\n')
        return

    if 'Records' not in rawjson.keys():
        sys.stderr.write(f'- ERROR: Input file {infile} does not appear to contain AWS CloudTrail records. Skipping file.\n')
        return

    for record in rawjson['Records']:
        outfh.write(f'{json.dumps(record)}\n')

parser = argparse.ArgumentParser(description='Process AWS CloudTrail logs into a format that SOF-ELK® can read, in ndjson form.')
parser.add_argument('-r', '--read', dest='infile', help='AWS CloudTrail log file to read, or a directory containing AWS CloudTrail log files. Files can be in native JSON or gzipped JSON.')
parser.add_argument('-w', '--write', dest='outfile', help='File to create containing processed AWS CloudTrail data.')
parser.add_argument('-f', '--force', dest='force_outfile', help=f'Force creating an output file in a location other than the default SOF-ELK® ingest location, {default_destdir}', default=False, action='store_true')
parser.add_argument('-a', '--append', dest='append', help='Append to the output file if it exists.', default=False, action='store_true')
parser.add_argument('-v', '--verbose', dest='verbose', help='Display progress and related status information while parsing input files.', default=False, action='store_true')
args = parser.parse_args()

if args.infile is None:
    sys.stderr.write('ERROR: No input file or root directory specified.\n')
    sys.exit(2)

if args.outfile is None:
    sys.stderr.write('ERROR: No output file specified.\n')
    sys.exit(2)
elif not args.outfile.startswith(default_destdir) and not args.force_outfile:
    sys.stderr.write(f'ERROR: Output file is not in {default_destdir}, which is the SOF-ELK® ingest location. Use "-f" to force creating a file in this location.\n')
    sys.exit(2)
elif not args.outfile.endswith('.json'):
    sys.stderr.write('ERROR: Output file does not end with ".json". SOF-ELK® requires this extension to process these logs. Exiting.\n')
    sys.exit(2)

input_files = []
if os.path.isfile(args.infile):
    input_files.append(args.infile)
elif os.path.isdir(args.infile):
    for root, dirs, files in os.walk(args.infile):
        for name in files:
            input_files.append(os.path.join(root, name))
else:
    sys.stderr.write('No input files could be processed. Exiting.\n')
    sys.exit(4)

if args.verbose:
    print(f'Found {len(input_files)} files to parse.')
    print()

if os.path.isfile(args.outfile) and args.append:
    outfh = open(args.outfile, 'a')
elif os.path.isfile(args.outfile) and not args.append:
    sys.stderr.write(f'ERROR: Output file {args.outfile} already exists. Use "-a" to append to the file at this location or specify a different filename.\n')
    sys.exit(3)
else:
    outfh = open(args.outfile, 'w')

fileno = 0
for infile in input_files:
    fileno += 1
    if args.verbose:
        print(f'- Parsing file: {infile} ({fileno} of {len(input_files)})')
    process_cloudtrail_file(infile, outfh)

print('Output complete.')
if not args.outfile.startswith(default_destdir):
    print(f'You must move/copy the generated file to the {default_destdir} directory before SOF-ELK® can process it.')
else:
    print('SOF-ELK® should now be processing the generated file - check system load and the Kibana interface to confirm.')
