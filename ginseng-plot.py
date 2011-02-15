#!/usr/bin/python
# coding=utf8

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
  print 'Start ' + start.strftime('%a %Y-%m-%d %H:%M')
  print 'End ' + end.strftime('%a %Y-%m-%d %H:%M')
  print ''

  plotstarttime = int(time.mktime(start.timetuple()))
  plotendtime = int(time.mktime(end.timetuple()))

  debug_message('Starttime ' + str(plotstarttime))
  debug_message('Endtime ' + str(plotendtime))

  plot_period = {}
  plot_period['start'] = plotstarttime
  plot_period['end'] = plotendtime
  plot_period['startstring'] = start.strftime('%a %Y-%m-%d %H:%M')
  plot_period['endstring'] = end.strftime('%a %Y-%m-%d %H:%M')
  return plot_period

#-----------------------------------------------------------------------------#
def is_measure_packet(node):
  return node.getAttribute('messageMode') == '102'

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

  for line in infile:
    line = line.rstrip('\n')
    data = line.split(' ')
    time = data[0]
    temp = data[1]
    nodeid = data[2]
    now = datetime.now()

    if (int(time) > interval['start']) and (int(time) < interval['end']):
      if not nodeid in filelist.keys():
        filelist[nodeid] = tempfile.NamedTemporaryFile(mode='w', dir=tempdir, prefix='ginseng-plotdata_' + nodeid + '_', delete=False)
        print 'File ' + filelist[nodeid].name + ' created'
        filelist[nodeid].write('# created ' + now.strftime('%a %Y-%m-%d %H:%M:%S') + '\n')
        filelist[nodeid].write('# node ' + nodeid + '\n')
      filelist[nodeid].write(time + ' ' + temp + '\n')

  for index in filelist.keys():
    filelist[index].flush()

#-----------------------------------------------------------------------------#
def main():
  cmdline_parser = argparse.ArgumentParser(description='Parses DispatchSink csv and outputs neat gnuplot graphs')
  cmdline_parser.add_argument('infiles', help='DispatchSink csv file', nargs='*')
  cmdline_parser.add_argument('--output', '-o', help='Output file [png]')
  cmdline_parser.add_argument('--debug', '-d', action='store_const', const=1, help='Print debug messages') 
  cmdline_parser.add_argument('--interval', '-i', help='Only plot defined interval. Supported values are Nhour, Nday, Nweek, Nmonth, Nyear, where N can be one of l for \'last\', c for \'last complete\' or e for \'last complete plus elapsed\'', default='all')

  args = cmdline_parser.parse_args()
  if args.debug:
    global debug
    debug = 1

  debug_message('debug: ' + str(args.debug))

  tempdir = tempfile.mkdtemp(prefix='ginsengtemp_')
  
  print ''
  print 'Created dir ' + tempdir

  plot_period = eval_time(args.interval)

  tmpfilelist = {}
  for index, infilename in enumerate(args.infiles):
    try:
      infile = open(infilename, mode='r')
      print 'Processing ' + infile.name + ' (' + str(index+1) + ' of ' + str(len(args.infiles)) + ')'
      process_file(infile, tmpfilelist, tempdir, plot_period)
    except IOError:
      print 'Couldn\'t find the file: ' + infile
      print 'Exiting...'
      sys.exit(1)

  if len(tmpfilelist) == 0:
    print ''
    print 'Nothing to plot'
    print 'Exiting...'
    sys.exit(1)

  if args.output == None:
    args.output = args.infiles[0].replace('.csv', '.png')

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

#Create files and invoke gnuplot
  temp_plotcmd = tempfile.NamedTemporaryFile(mode='w', dir=tempdir, prefix='ginseng-plotcmd_', delete=False)
  print 'Created tempfile ' + temp_plotcmd.name + ' as script for gnuplot'

  interval = 'Last '
  if args.interval.endswith('hour'):
    interval = interval + 'hour'
  elif args.interval.endswith('day'):
    interval = interval + 'day'
  elif args.interval.endswith('week'):
    interval = interval + 'week'
  elif args.interval.endswith('month'):
    interval = interval + 'month'
  elif args.interval.endswith('year'):
    interval = interval + 'year'
  else:
    interval + 'All'

  now = datetime.now()
  temp_plotcmd.write('# created ' + now.strftime('%a %Y-%m-%d %H:%M:%S') + '\n')
  temp_plotcmd.write('set terminal png size 1280,1024\n')
  temp_plotcmd.write('set output \'' + os.path.abspath(args.output) + '\'\n')
  temp_plotcmd.write('set xdata time\n')
  temp_plotcmd.write('set xlabel \'Time\'\n')
  temp_plotcmd.write('set ylabel \'Temperature [°C]\'\n')
  temp_plotcmd.write('set timefmt \'%s\'\n')
  temp_plotcmd.write('set grid\n')
  temp_plotcmd.write('set title \'' + interval + ' (From ' + plot_period['startstring'] + ' till ' + plot_period['endstring'] + ')\'\n')
  temp_plotcmd.write('plot ')
  
  firstentry = True

  for nodeid in tmpfilelist.keys():
    if firstentry:
      firstentry = False
    else:
      temp_plotcmd.write(',\\\n')
    temp_plotcmd.write('\'' + tmpfilelist[nodeid].name + '\' using ($1 + 90000):2 title \"Node ' + nodeid + '\" smooth unique')
    tmpfilelist[nodeid].close()

  temp_plotcmd.write('\n')
  temp_plotcmd.flush()

  os.system('gnuplot ' + temp_plotcmd.name)

  temp_plotcmd.close()

if __name__ == "__main__":
  main()
