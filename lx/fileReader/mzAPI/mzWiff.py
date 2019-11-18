#Copyright 2008 Dana-Farber Cancer Institute
#multiplierz is distributed under the terms of the GNU Lesser General Public License
#
#This file is part of multiplierz.
#
#multiplierz is free software: you can redistribute it and/or modify
#it under the terms of the GNU Lesser General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#multiplierz is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public License
#along with multiplierz.  If not, see <http://www.gnu.org/licenses/>.



import wiffbridge
import re, os
import pickle
from mzAPI import mzScan, mzFile as mzAPImzFile

class mzFile(mzAPImzFile):
    """Base helper class for WIFF files"""

    def __init__(self, data_file, sample=1, period=1):
        self.file_type = 'wiff'
        self.data_file = data_file

        self.file_id = wiffbridge.open(data_file, sample, period)
        self.info_file = ''
        self.info_scans = ()
        if os.path.exists(data_file + '.mzi'):
            self.info_file = data_file + '.mzi'
            info_fh = open(self.info_file)
            self.info_scans = pickle.load(info_fh)
            info_fh.close()

    def close(self):
        wiffbridge.close(self.file_id)

    def scan_list(self, start_time, stop_time, start_mz=0, stop_mz=99999):
        if not start_time or not stop_time:
            (file_start_time, file_stop_time) = self.time_range()
        if not start_time:
            start_time = file_start_time
        if not stop_time:
            stop_time = file_stop_time

        scan_list = []
        all_scans = []
        if self.info_file != '':
            all_scans = self.info_scans.filter(list_key='time', value_range=[start_time - 0.00001, stop_time])
            for item in all_scans:
                if item['scan_type'] == 'MS1' or (item['mz'] >= start_mz and item['mz'] <= stop_mz):
                    scan_list.append((item['time'], item['mz']))

        else:
            all_scans = wiffbridge.scanInfo(self.file_id, start_time, stop_time)
            all_scans.sort()

            for (time, mz, experiment, cycle) in all_scans:
                if time > stop_time:
                    break
                if experiment == 1:
                    scan_list.append((time, mz))
                else:
                    if mz >= start_mz and mz <= stop_mz:
                        scan_list.append((time, mz))

        scan_list.sort()
        return scan_list

    def scan_info(self, start_time, stop_time, start_mz=0, stop_mz=99999):

        if stop_time == 0:
            stop_time = start_time

        scan_list = []
        all_scans = []
        scan_mode = 'p'
        if self.info_file != '':
            all_scans = self.info_scans.filter(list_key='time', value_range=[start_time - 0.00001, stop_time])
            for item in all_scans:
                if item['scan_type'] == 'MS1' or (item['mz'] >= start_mz and item['mz'] <= stop_mz):
                    scan_list.append((item['time'], item['mz'], item['scan_name'], item['scan_type'], item['scan_mode']))

        else:
            all_scans = wiffbridge.scanInfo(self.file_id, start_time, stop_time)
            all_scans.sort()

            for (time, mz, experiment, cycle) in all_scans:
                if time > stop_time:
                    break
                if experiment == 1:
                    scan_list.append((time, mz, (int(cycle),int(experiment)), 'MS1', scan_mode))
                else:
                    if mz >= start_mz and mz <= stop_mz:
                        scan_list.append((time, mz, (int(cycle),int(experiment)), 'MS2', scan_mode))

        scan_list.sort()

        return scan_list

    def scan_time_from_scan_name(self, cycle_exp):
        #cycle_exp = (cycle, experiment)
        (cycle, experiment) = cycle_exp
        if self.info_file != '':
            time = self.info_scans.filter(list_key='scan_name', value_list=[(cycle, experiment)])[0]['time']
        else:
            time = wiffbridge.timeForScan(self.file_id, int(experiment), int(cycle))
        return time

    def scan(self, time, add_zeros=True):
        # 'add_zeros' is on by default, adds the missing zero data points

        scan_mode = 'p'
        if self.info_file != '':
            closest_item = self.info_scans.closest(key='time', value=time)
            scan_time = closest_item['time']
            (cycle, experiment) = closest_item['scan_name']
            scan_mode = closest_item['scan_mode']
            mz = closest_item['mz']
        else:
            (scan_time, mz, experiment, cycle) = wiffbridge.scanForTime(self.file_id, time)

        scan = wiffbridge.scan(self.file_id, cycle, experiment)

        if add_zeros:
            scan.sort()
            scan_data = [(scan[0][0]-0.00001,0)] #First Point
            for i,sc in enumerate(scan[:-1]):
                if (scan[i+1][0] - sc[0]) > 0.03:
                    #Add data point, zero right after it, zero right before next point
                    scan_data.extend((sc,(sc[0]+0.00001,0), (scan[i+1][0]-0.00001,0)))
                else:
                    scan_data.append(sc)  #Add data point

            #Add last data point
            scan_data.extend((scan[-1],(scan[-1][0]+0.00001,0)))
        else:
            scan_data = scan

        return mzScan(scan_data, scan_time, scan_mode, mz)

    def xic(self, start_time, stop_time, start_mz, stop_mz, filter=None):
        #Until I see a use for restricting the XIC to an experiment I will not bother
        #using the filter parameter...
        xic_data = wiffbridge.ric(self.file_id, start_time, stop_time, start_mz, stop_mz)
        return xic_data

    def time_range(self):
        if self.info_file != '':
            time_list = self.info_scans.sort_by_field('time')
            time_range = (time_list[0]['time'],time_list[-1]['time'])
        else:
            time_range = wiffbridge.timeRange(self.file_id)
        return time_range
