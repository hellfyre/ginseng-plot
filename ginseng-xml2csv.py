#!/usr/bin/python
# coding=utf8

import argparse
import os
import sys
import xml.dom.minidom

debug = 0

#-----------------------------------------------------------------------------#
def debug_message(message):
  global debug
  if debug:
    print '[DEBUG] ' + message

#-----------------------------------------------------------------------------#
def is_measure_packet(node):
  return node.getAttribute('messageMode') == '102'

#-----------------------------------------------------------------------------#
def process_file(infilename, outfile, last_temp, timezone_seconds):
  debug_message('Parsing file...')
  xmldoc = xml.dom.minidom.parse(infilename)
  debug_message('Done parsing')

  eventlogs = xmldoc.getElementsByTagName('WSNsEventLog')
  if eventlogs.length == 1:
    debug_message('WSN event log node found, processing...')
    eventlog = eventlogs[0]
  else:
    if eventlogs.length > 1:
      print 'Not implemented yet: Processing more than one WSNsEventLog node. Exiting...'
    else:
      print 'No WSNsEventLog nodes found. Exiting...'
    sys.exit(1)

# get all wsnMessages from WNSsEventLog
  messages = eventlog.getElementsByTagName('wsnMessage')
# free memory
  eventlogs = None
  eventlog = None

# filter messages
  for message in messages:
    if is_measure_packet(message):
      parameters = message.getElementsByTagName('parameter')

      paramcount = 0
      temp = 0
      time = 0
      nodeid = 0

      for parameter in parameters:
        if parameter.attributes['name'].value == 'genTime':
          time_int = int(parameter.childNodes[0].data[:-3]) + timezone_seconds
          time = str(time_int)
          paramcount += 1
        if parameter.attributes['name'].value == 'temp':
          temp_float = -39.6 + 0.01 * int(parameter.childNodes[0].data)
          temp = str(temp_float)
          paramcount += 1
        if parameter.attributes['name'].value == 'hwid':
          nodeid = parameter.childNodes[0].data
          paramcount += 1

      if paramcount == 3:
        if nodeid in last_temp.keys():
          if last_temp[nodeid]['time'] < time:
            last_temp[nodeid]['time'] = time
            last_temp[nodeid]['temp'] = temp
        else:
          debug_message('new node encountered: ' + nodeid)
          last_temp[nodeid] = {}
          last_temp[nodeid]['time'] = time
          last_temp[nodeid]['temp'] = temp

        outfile.write(time + ' ' + temp + ' ' + nodeid + '\n')
        continue # with next message/packet as soon as time, temp and id are extracted

#-----------------------------------------------------------------------------#
def main():
  cmdline_parser = argparse.ArgumentParser(description='Parses DispatchSink xml and outputs csv files')
  cmdline_parser.add_argument('infiles', help='DispatchSink xml file', nargs='*')
  cmdline_parser.add_argument('--debug', '-d', action='store_const', const=1, help='Print debug messages') 
  cmdline_parser.add_argument('--lasttempfile', '-l', help='File to write latest temperatures to')
  cmdline_parser.add_argument('--output', '-o', help='Output dir for csv files', required=True)
  cmdline_parser.add_argument('--timezone', '-t', help='The local timezone in hours from GMT', default='0')

  args = cmdline_parser.parse_args()
  if args.debug:
    global debug
    debug = 1
  timezone_seconds = int(args.timezone) * 3600

  debug_message('debug: ' + str(args.debug))

  print ''

  if not os.path.exists(args.output):
    print 'Output directory doesn\'t exist'
    print 'Exiting...'
    sys.exit(1)

  last_temp = {}
  for index, infilename in enumerate(args.infiles):
    print 'Input file (' + str(index+1) + ' of ' + str(len(args.infiles)) + '): ' + infilename,
    outfilename = os.path.basename(infilename.replace('.xml', '.csv'))
    outfilename = os.path.normpath(args.output) + os.sep + outfilename
    if os.path.exists(outfilename):
      print 'already processed'
    else:
      try:
        outfile = open(outfilename, mode='w')
      except IOError:
        print 'Error writing to ' + outfilename + '. Probably a permission problem'
        print 'Exiting...'
        sys.exit(1)
      print 'processing...'
      process_file(infilename, outfile, last_temp, timezone_seconds)
      print 'Saved to ' + outfile.name

  if not args.lasttempfile == None and len(last_temp) > 0:
    try:
      lasttemp_outfile = open(args.lasttempfile, mode='w')
    except IOError:
      print 'Error writing to ' + args.lasttempfile+ '. Probably a permission problem'
      print 'Exiting...'
      sys.exit(1)
    for nodeid in last_temp.keys():
      temp = last_temp[nodeid]['temp']
      lasttemp_outfile.write(nodeid + ' ' + str(temp) + '\n')
    lasttemp_outfile.flush()
    lasttemp_outfile.close()
    print 'Latest temperatures written to ' + args.lasttempfile

if __name__ == "__main__":
  main()
