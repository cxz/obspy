# -*- coding: utf-8 -*-
#-------------------------------------------------------------------
# Filename: waveform.py
#  Purpose: Waveform plotting for obspy.Stream objects
#   Author: Lion Krischer
#    Email: krischer@geophysik.uni-muenchen.de
#
# Copyright (C) 2008-2010 Lion Krischer
#---------------------------------------------------------------------
"""
Waveform plotting for obspy.Stream objects.

GNU General Public License (GPL)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
"""

from obspy.core.util import UTCDateTime
import StringIO
import matplotlib.pyplot as plt
import numpy as N

def plotWaveform(stream_object, outfile=None, format=None,
               size=(800, 250), starttime=False, endtime=False,
               dpi=100, color='k', bgcolor='w',
               transparent=False, minmaxlist=False,
               number_of_ticks=5, tick_format = '%H:%M:%S', tick_rotation=0):
    """
    Creates a graph of any given ObsPy Stream object. It either saves the image
    directly to the file system or returns an binary image string.
    
    For all color values you can use legit html names, html hex strings
    (e.g. '#eeefff') or you can pass an R , G , B tuple, where each of
    R , G , B are in the range [0,1]. You can also use single letters for
    basic builtin colors ('b' = blue, 'g' = green, 'r' = red, 'c' = cyan,
    'm' = magenta, 'y' = yellow, 'k' = black, 'w' = white) and gray shades
    can be given as a string encoding a float in the 0-1 range.
    
    @param stream_object: ObsPy Stream object.
    @param outfile: Output file string. Also used to automatically
        determine the output format. Currently supported is emf, eps, pdf,
        png, ps, raw, rgba, svg and svgz output.
        Defaults to None.
    @param format: Format of the graph picture. If no format is given the
        outfile parameter will be used to try to automatically determine
        the output format. If no format is found it defaults to png output.
        If no outfile is specified but a format is than a binary
        imagestring will be returned.
        Defaults to None.
    @param size: Size tupel in pixel for the output file. This corresponds
        to the resolution of the graph for vector formats.
        Defaults to 800x250 px.
    @param starttime: Starttime of the graph as a datetime object. If not
        set the graph will be plotted from the beginning.
        Defaults to False.
    @param endtime: Endtime of the graph as a datetime object. If not set
        the graph will be plotted until the end.
        Defaults to False.
    @param dpi: Dots per inch of the output file. This also affects the
        size of most elements in the graph (text, linewidth, ...).
        Defaults to 100.
    @param color: Color of the graph. If the supplied parameter is a
        2-tupel containing two html hex string colors a gradient between
        the two colors will be applied to the graph.
        Defaults to 'k' (black).
    @param bgcolor: Background color of the graph. No gradients are supported
        for the background.
        Defaults to 'w' (white).
    @param transparent: Make all backgrounds transparent (True/False). This
        will overwrite the bgcolor param.
        Defaults to False.
    @param minmaxlist: A list containing minimum, maximum and timestamp
        values. If none is supplied it will be created automatically.
        Useful for caching.
        Defaults to False.
    @param number_of_ticks: Number of the ticks on the time scale to display.
        Defaults to 5.
    @param tick_format: Format of the time ticks according to strftime methods.
        Defaults to '%H:%M:%S'.
    @param tick_rotation: Number of degrees of the rotation of the ticks an the
        time scale. Ticks with big rotations might be cut off depending on the
        tick_format.
        Defaults to 0.
    """
    # Turn interactive mode off or otherwise only the first plot will be fast.
    plt.ioff()
    # Get a list with minimum and maximum values.
    if not minmaxlist:
        minmaxlist = _getMinMaxList(stream_object=stream_object,
                                                width=size[0],
                                                starttime=starttime,
                                                endtime=endtime)
    starttime = minmaxlist[0]
    endtime = minmaxlist[1]
    stepsize = (endtime - starttime) / size[0]
    minmaxlist = minmaxlist[2:]
    # Get all stats attributes any make a new list.
    stats_list = []
    for _i in minmaxlist:
        stats_list.append(_i.pop())
    length = len(minmaxlist[0])
    # Setup figure and axes
    plt.figure(num=None, figsize=(float(size[0]) / dpi,
                     float(size[1]) / dpi))
    suptitle = '%s - %s' % (UTCDateTime(starttime).strftime('%x %X'), 
                           UTCDateTime(endtime).strftime('%x %X'))
    plt.suptitle(suptitle, x = 0.02, y = 0.96, fontsize='small',
                 horizontalalignment = 'left')
    # Determine range for the y axis. This will ensure that at least 98% of all
    # values are fully visible.
    # This also assures that all subplots have the same scale on the y-axis.
    minlist = []
    maxlist = []
    for _i in minmaxlist:
        minlist.extend([j[0] for j in _i])
        maxlist.extend([j[1] for j in _i])
    minlist.sort()
    maxlist.sort()
    miny = minlist[0]
    maxy = maxlist[-1]
    # Determines the 2 and 98 percent quantiles of min and max values.
    eighty_nine_miny = minlist[int(int(length * 0.02))]
    eighty_nine_maxy = maxlist[int(int(length * 0.98))]
    # Calculate 98%-range.
    yrange = eighty_nine_maxy - eighty_nine_miny
    # If the outer two percent are more than 10 times bigger discard them.
    if miny + 10 * yrange < maxy:
        miny = eighty_nine_miny
        maxy = eighty_nine_maxy
    else:
        yrange = maxy - miny
    miny = miny - (yrange * 0.1)
    maxy = maxy + (yrange * 0.1)
    # Create the location of the ticks.
    tick_location = []
    x_range = endtime-starttime
    if number_of_ticks > 1:
        for _i in xrange(number_of_ticks):
            tick_location.append(starttime + _i*x_range/(number_of_ticks-1))
    elif number_of_ticks == 1:
        tick_location.append(starttime + x_range/2)
    # Create tick names
    tick_names = [UTCDateTime(_i).strftime(tick_format) for _i in \
                  tick_location]
    if number_of_ticks > 1:
        # Adjust first tick to be visible.
        tick_location[0] = tick_location[0]+0.5*x_range/size[0]
    for _j in range(len(minmaxlist)):
        plt.subplot(len(minmaxlist), 1, _j+1)
        # Make title
        cur_stats = stats_list[_j]
        title_text = '%s.%s.%s, %s Hz, %s samples' % (cur_stats.network,
            cur_stats.station, cur_stats.channel, cur_stats.sampling_rate,
            cur_stats.npts)
        plt.title(title_text, horizontalalignment = 'left',
                  fontsize = 'small', verticalalignment = 'center')
        # Set axes and disable ticks on the y axis.
        plt.ylim(miny, maxy)
        plt.xlim(starttime, endtime)
        plt.yticks([])
        plt.xticks(tick_location, tick_names, rotation = tick_rotation, 
                   fontsize = 'small')
        # Overwrite the background gradient if transparent is set.
        if transparent:
            bgcolor = None
        # Clone color for looping.
        loop_color = color
        # Draw horizontal lines.
        for _i in range(length):
            #Make gradient if color is a 2-tupel.
            if type(loop_color) == type((1, 2)):
                #Convert hex values to integers
                r1 = int(loop_color[0][1:3], 16)
                r2 = int(loop_color[1][1:3], 16)
                delta_r = (float(r2) - float(r1)) / length
                g1 = int(loop_color[0][3:5], 16)
                g2 = int(loop_color[1][3:5], 16)
                delta_g = (float(g2) - float(g1)) / length
                b1 = int(loop_color[0][5:], 16)
                b2 = int(loop_color[1][5:], 16)
                delta_b = (float(b2) - float(b1)) / length
                new_r = hex(int(r1 + delta_r * _i))[2:]
                new_g = hex(int(g1 + delta_g * _i))[2:]
                new_b = hex(int(b1 + delta_b * _i))[2:]
                if len(new_r) == 1:
                    new_r = '0' + new_r
                if len(new_g) == 1:
                    new_g = '0' + new_g
                if len(new_b) == 1:
                    new_b = '0' + new_b
                #Create color string
                bar_color = '#' + new_r + new_g + new_b
            else:
                bar_color = color
            #Calculate relative values needed for drawing the lines.
            yy = (float(minmaxlist[_j][_i][0]) - miny) / (maxy - miny)
            xx = (float(minmaxlist[_j][_i][1]) - miny) / (maxy - miny)
            #Draw actual data lines.
            plt.axvline(x=minmaxlist[_j][_i][2], ymin=yy, ymax=xx,
                        color=bar_color)
    #Save file.
    if outfile:
        #If format is set use it.
        if format:
            plt.savefig(outfile, dpi=dpi, transparent=transparent,
                facecolor=bgcolor, edgecolor=bgcolor, format=format)
        #Otherwise try to get the format from outfile or default to png.
        else:
            plt.savefig(outfile, dpi=dpi, transparent=transparent,
                facecolor=bgcolor, edgecolor=bgcolor)
    #Return an binary imagestring if outfile is not set but format is.
    if not outfile:
        if format:
            imgdata = StringIO.StringIO()
            plt.savefig(imgdata, dpi=dpi, transparent=transparent,
                    facecolor=bgcolor, edgecolor=bgcolor, format=format)
            imgdata.seek(0)
            return imgdata.read()
        else:
            plt.show()


def _getMinMaxList(stream_object, width, starttime=None,
                   endtime=None):
    """
    Creates a list with tuples containing a minimum value, a maximum value
    and a timestamp in microseconds.
    
    Only values between the start- and the endtime will be calculated. The
    first two items of the returned list are the actual start- and endtimes
    of the returned list. This is needed to cope with all possible Stream
    types.
    The returned timestamps are the mean times of the minmax value pair.
    
    @requires: The Mini-SEED file has to contain only one trace. It may
        contain gaps and overlaps and it may be arranged in any order but
        the first and last records must be in chronological order as they
        are used to determine the start- and endtime.
    
    @param stream_object: ObsPy Stream object.
    @param width: Number of tuples in the list. Corresponds to the width
        in pixel of the graph.
    @param starttime: Starttime of the List/Graph as a Datetime object. If
        none is supplied the starttime of the file will be used.
        Defaults to None.
    @param endtime: Endtime of the List/Graph as a Datetime object. If none
        is supplied the endtime of the file will be used.
        Defaults to None.
    """
    # Sort stream
    stream_object.sort()
    all_traces = stream_object.traces
    # Create a sorted list of traces with one item for each identical trace
    # which contains all obspy.Trace objects that belong to the same trace.
    sorted_trace_list = []
    for _i in xrange(len(all_traces)):
        if len(sorted_trace_list) == 0:
            sorted_trace_list.append([all_traces[_i]])
        else:
            cur_trace_stats = all_traces[_i].stats
            last_trace_stats = sorted_trace_list[-1][-1].stats
            if cur_trace_stats.station == last_trace_stats.station and \
               cur_trace_stats.network == last_trace_stats.network and \
               cur_trace_stats.channel == last_trace_stats.channel:
                sorted_trace_list[-1].append(all_traces[_i])
            else:
                sorted_trace_list.append([all_traces[_i]])
    # Calulate start- and endtime and other parameters important for the whole
    # minmaxlist.
    # Get start- and endtime and convert them to UNIX timestamp.
    if not starttime:
        plot_starttime = min([_i[0].stats['starttime'] for _i in \
                         sorted_trace_list]).timestamp
    else:
        plot_starttime = starttime.timestamp
    if not endtime:
        # The endtime of the last trace in the previously sorted list is
        # supposed to be the endtime of the plot.
        plot_endtime = max([_i[-1].stats['endtime'] for _i in \
                         sorted_trace_list]).timestamp
    else:
        plot_endtime = endtime.timestamp
    # Calculate time for one pixel.
    stepsize = (plot_endtime - plot_starttime) / width
    # First two items are start- and endtime.
    full_minmaxlist = [plot_starttime, plot_endtime]
    for traces in sorted_trace_list:
        # Reset loop times
        starttime = plot_starttime
        endtime = plot_endtime
        minmaxlist= []
        # While loop over the plotting duration.
        while starttime < endtime:
            pixel_endtime = starttime + stepsize
            maxlist = []
            minlist = []
            # Inner Loop over all traces.
            for _i in traces:
                a_stime = _i.stats['starttime'].timestamp
                a_etime = _i.stats['endtime'].timestamp
                npts = _i.stats['npts']
                # If the starttime is bigger than the endtime of the current
                # trace delete the item from the list.
                if starttime > a_etime:
                    pass
                elif starttime < a_stime:
                    # If starttime and endtime of the current pixel are too
                    # small than leave the list.
                    if pixel_endtime < a_stime:
                        #Leave the loop.
                        pass
                    # Otherwise append the border to tempdatlist.
                    else:
                        end = float((pixel_endtime - a_stime)) / \
                              (a_etime - a_stime) * npts
                        if end > a_etime:
                            end = a_etime
                        maxlist.append(_i.data[0 : int(end)].max())
                        minlist.append(_i.data[0 : int(end)].min())
                # Starttime is right in the current trace.
                else:
                    # Endtime also is in the trace. Append to tempdatlist.
                    if pixel_endtime < a_etime:
                        start = float((starttime - a_stime)) / (a_etime - \
                                                    a_stime) * npts
                        end = float((pixel_endtime - a_stime)) / \
                              (a_etime - a_stime) * npts
                        maxlist.append(_i.data[int(start) : int(end)].max())
                        minlist.append(_i.data[int(start) : int(end)].min())
                    # Endtime is not in the trace. Append to tempdatlist.
                    else:
                        start = float((starttime - a_stime)) / (a_etime - \
                                                    a_stime) * npts
                        maxlist.append(_i.data[int(start) : \
                                               npts].max())
                        minlist.append(_i.data[int(start) : \
                                               npts].min())
            # If empty list do nothing.
            if minlist == []:
                pass
            # If not empty append min, max and timestamp values to list.
            else:
                minmaxlist.append((min(minlist), max(maxlist),
                                   starttime + 0.5 * stepsize))
            # New starttime for while loop.
            starttime = pixel_endtime
        # Appends the stats dictionary to each different trace.
        minmaxlist.append(traces[0].stats)
        full_minmaxlist.append(minmaxlist)
    return full_minmaxlist