#!/usr/bin/python
# coding=utf8

import argparse
from datetime import datetime, timedelta
import os
import sys

debug = 0

#-----------------------------------------------------------------------------#
def debug_message(message):
  global debug
  if debug:
    print '[DEBUG] ' + message

#-----------------------------------------------------------------------------#
def main():
  cmdline_parser = argparse.ArgumentParser(description='Generates an HTML file to view graphs')
  cmdline_parser.add_argument('infile', help='Lastest temperatures')
  cmdline_parser.add_argument('--output', '-o', help='Output file [html]')
  cmdline_parser.add_argument('--debug', '-d', action='store_const', const=1, help='Print debug messages') 

  args = cmdline_parser.parse_args()
  if args.debug:
    global debug
    debug = 1

  debug_message('debug: ' + str(args.debug))

  try:
    infile = open(args.infile, mode='r')
  except IOError:
    print 'Couldn\'t find the file: ' + infile
    print 'Exiting...'
    sys.exit(1)

  try:
    outfile = open(args.output, mode='w')
  except IOError:
    print 'Error writing to ' + args.output + '. Probably a permission problem'
    print 'Exiting...'
    sys.exit(1)

  now = datetime.now()
  outfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">\n')
  outfile.write('<html>\n')
  outfile.write('<head>\n')
  outfile.write('  <title>Ginseng Temperature Graphs</title>\n')
  outfile.write('</head>\n')
  outfile.write('\n')
  outfile.write('<body>\n')
  outfile.write('  <p>\n')
  outfile.write('    <a href="hourly.png"><img src="hourly.png" width=320 height=240 alt="Hourly"></a>\n')
  outfile.write('    <a href="daily.png"><img src="daily.png" width=320 height=240 alt="Daily"></a>\n')
  outfile.write('    <a href="weekly.png"><img src="weekly.png" width=320 height=240 alt="Weekly"></a>\n')
  outfile.write('    <a href="monthly.png"><img src="monthly.png" width=320 height=240 alt="Monthly"></a>\n')
  outfile.write('    <a href="yearly.png"><img src="yearly.png" width=320 height=240 alt="Yearly"></a>\n')
  outfile.write('    <a href="lagederknoten.jpg"><img src="lagederknoten.jpg" width=320 height=240 alt="Lage der Knoten"></a>\n')
  outfile.write('  </p>\n')
  outfile.write('  <p>\n')
  outfile.write('    Latest temperatures recorded ' + now.strftime('%a %Y-%m-%d %H:%M:%S') + '\n')
  outfile.write('    <table border=1>\n')
  outfile.write('      <thead>\n')
  outfile.write('        <tr>\n')
  outfile.write('          <th>Node</th>\n')
  outfile.write('          <th>Temperature</th>\n')
  outfile.write('        </tr>\n')
  outfile.write('      </thead>\n')
  outfile.write('      <tbody>\n')
  for line in infile:
    line = line.rstrip('\n')
    data = line.split(' ')
    outfile.write('        <tr>\n')
    outfile.write('          <td>' + data[0] + '</td>\n')
    outfile.write('          <td>' + data[1] + '</td>\n')
    outfile.write('        </tr>\n')
  outfile.write('      </tbody>\n')
  outfile.write('    </table>\n')
  outfile.write('  </p>\n')
  outfile.write('</body>\n')
  outfile.write('</html>\n')
  outfile.flush()
  outfile.close()

  infile.close()

if __name__ == "__main__":
  main()
