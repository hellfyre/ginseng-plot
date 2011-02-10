#!/usr/bin/python

import argparse
from datetime import datetime, timedelta
import os
import sys
import tempfile
import time
import xml.dom.minidom

debug = 0

#-----------------------------------------------------------------------------#
def debug_message(message):
  global debug
  if debug:
    print '[DEBUG] ' + message

#-----------------------------------------------------------------------------#
def eval_time(interval):
#evaluate time constraints
  now = datetime.now()
  plotstarttime = 0
  plotendtime = 0
  start = None
  end = None
  delta = None

  if interval.endswith('hour'):
    delta = timedelta(hours = 1)
  elif interval.endswith('day'):
    delta = timedelta(days = 1)
  elif interval.endswith('week'):
    delta = timedelta(weeks = 1)
  elif interval.endswith('month'):
    delta = timedelta(weeks = 4)
  elif interval.endswith('year'):
    delta = timedelta(days = 365)

  if interval.startswith('l'):
    end = now
    start = end - delta
  elif interval.startswith('c'):
    end = normalize_date(now, interval)
    start = normalize_date(end - delta, interval)
  elif interval.startswith('e'):
    end = now
    start = normalize_date(end - delta, interval)

  if interval == 'all':
    end = now
    start = datetime(1900, 1, 1)

  print ''
  print 'Plotting period:'
  print 'Start ' + start.strftime('%a %Y-%m-%d %H:%M:%S')
  print 'End ' + end.strftime('%a %Y-%m-%d %H:%M:%S')
  print ''

  plotstarttime = int(1000 * time.mktime(start.timetuple()))
  plotendtime = int(1000 * time.mktime(end.timetuple()))

  debug_message('Starttime ' + str(plotstarttime))
  debug_message('Endtime ' + str(plotendtime))

  plot_period = {}
  plot_period['start'] = plotstarttime
  plot_period['end'] = plotendtime
  return plot_period

#-----------------------------------------------------------------------------#
def is_element_node(node):
  return node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE

#-----------------------------------------------------------------------------#
def is_measure_packet(node):
  return node.getAttribute('messageMode') == '102'

#-----------------------------------------------------------------------------#
def merge(data):
  merged_list = []
  merged_nodes_enc = []
  for date in data:
    for measurement in date[0]:
      merged_list.append(measurement)
    for nodeid in date[1]:
      if not nodeid in merged_nodes_enc:
        merged_nodes_enc.append(nodeid)

  return (merged_list, merged_nodes_enc)

#-----------------------------------------------------------------------------#
def normalize_date(date, interval):
  if interval.endswith('hour'):
    return date.replace(minute=0, second=0, microsecond=0)
  elif interval.endswith('day'):
    return date.replace(hour=0, minute=0, second=0, microsecond=0)
  elif interval.endswith('week'):
    if (date.day - date.weekday()) > 0:
      return date.replace(day=(date.day - date.weekday()), hour=0, minute=0, second=0, microsecond=0)
    else:
      delta = timedelta(weeks = 1)
      return date.replace(day=(date.day + date.isoweekday()), hour=0, minute=0, second=0, microsecond=0) - delta
  elif interval.endswith('month'):
    return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
  elif interval.endswith('year'):
    return date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

#-----------------------------------------------------------------------------#
def process_file(infile, filelist, tempdir, interval):
  xml = xml.dom.minidom.parse(infile)
  eventlogs = xml.getElementsByTagName('WSNsEventLog')
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
  data = {}
  last_temp = {}
  for message in messages:
    if is_measure_packet(message):
      parameters = packet.getElementsByTagName('parameter')

      paramcount = 0
      temp = 0
      time = 0
      nodeid = 0

      for parameter in parameters:
        if parameter.attributes['name'].value == 'genTime':
          time = parameter.childNodes[0].data
          paramcount += 1
        if parameter.attributes['name'].value == 'temp':
          temp = parameter.childNodes[0].data
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
        if (time > interval['start']) and (time < interval['end']):
          #TODO write to file, remember hwid
        continue # with next message/packet as soon as time, temp and id are extracted

# free memory
  messages = None


#-----------------------------------------------------------------------------#
def process_xml(xml, interval):

#-----------------------------------------------------------------------------#
def main():
  cmdline_parser = argparse.ArgumentParser(description='Parses DispatchSink xml and outputs neat gnuplot graphs')
  cmdline_parser.add_argument('infiles', help='DispatchSink xml file', nargs='*')
  cmdline_parser.add_argument('--output', '-o', help='Output file [png]')
  cmdline_parser.add_argument('--debug', '-d', action='store_const', const=1, help='Print debug messages') 
  cmdline_parser.add_argument('--interval', '-i', help='Only plot defined interval. Supported values are Nhour, Nday, Nweek, Nmonth, Nyear, where N can be one of l for \'last\', c for \'last complete\' or e for \'last complete plus elapsed\'', default='all')

  args = cmdline_parser.parse_args()
  if args.debug:
    global debug
    debug = 1

  debug_message('debug: ' + str(args.debug))

  tempdir = tempfile.mkdtemp(prefix='ginsengtemp')

  print ''
  for infile in args.infiles:
    print 'Input file: ' + infile

  plot_period = eval_time(args.interval)

  tmpfilelist = {}
  for index, infile in enumerate(args.infiles):
    try:
      print 'Processing ' + infile + ' (' + str(index) + ' of ' + str(len(args.infiles)) + ')'
      process_file(infile, tmpfilelist, tempdir, plot_period)
    except IOError:
      print 'Couldn\'t find the file: ' + infile
      print 'Exiting...'
      sys.exit(1)

  if args.output == None:
    args.output = args.infiles[0].replace('.xml', '') + '.png'

  if os.path.exists(args.output):
    print 'Output file ' + args.output + ' already exists. Overwriting...'

  try:
    outfile = open(args.output, mode='w')
    outfile.close()
    os.remove(args.output)
  except IOError:
    print 'Error writing to ' + args.output + '. Probably a permission problem'
    print 'Exiting...'
    sys.exit(1)

  print 'Output file: ' + args.output

  data = []
  for xmldoc in xmldocs:
    data.append(process_xmldoc(xmldoc))

  merged = merge(data)
#free memory
  xmldocs = None
  data = None

#  for measurement in merged[0]:
#    if (int(measurement[0]) < plotstarttime):
#      debug_message('Deleting record (' + measurement[0] + ', ' + measurement[1] + ', ' + measurement[2] + ') too old')
#      merged[0].remove(measurement)
#    if (int(measurement[0]) > plotendtime):
#      debug_message('Deleting record (' + measurement[0] + ', ' + measurement[1] + ', ' + measurement[2] + ') too young')
#      merged[0].remove(measurement)
      
#Create files and invoke gnuplot
  temp_plotcmd = tempfile.NamedTemporaryFile(mode='w', prefix='ginseng-plotcmd_', delete=False)
  print 'Created tempfile ' + temp_plotcmd.name + ' as script for gnuplot'

  temp_plotcmd.write('set terminal png\n')
  temp_plotcmd.write('set output \'' + os.path.abspath(args.output) + '\'\n')
  temp_plotcmd.write('set xdata time\n')
  temp_plotcmd.write('set xlabel \'Time\'\n')
  temp_plotcmd.write('set ylabel \'Temperature\'\n')
  temp_plotcmd.write('set timefmt "%s"\n')
  temp_plotcmd.write('set grid\n')

  filelist = []
  for node in merged[1]:
    filelist.append(tempfile.NamedTemporaryFile(mode='w', prefix='ginseng-plotdata_' + node + '_', delete=False))
    print 'Created tempfile ' + filelist[-1].name + ' for nodeid ' + node
    filelist[-1].write('# node ' + node + '\n')
    for measurement in merged[0]:
      if measurement[2] == node:
        filelist[-1].write(measurement[0][:-3] + ' ' + measurement[1] + '\n')
        merged[0].remove(measurement)
    filelist[-1].flush()
    if len(filelist) == 1:
      temp_plotcmd.write('plot ')
    else:
      temp_plotcmd.write(',\\\n')
    temp_plotcmd.write('\'' + filelist[-1].name + '\' using 1:2 title \"Node ' + node + '\" smooth unique')

  temp_plotcmd.write('\n')
  temp_plotcmd.flush()


  os.system('gnuplot ' + temp_plotcmd.name)

  temp_plotcmd.close()
  for file in filelist:
    file.close()

if __name__ == "__main__":
  main()
