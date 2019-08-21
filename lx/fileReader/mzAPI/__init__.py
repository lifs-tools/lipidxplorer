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

"""Common API for multiple mass spectrometry instrument file access

mzAPI unifies access to MS data files by referring to scans by time.
mzAPI uses helper files that access the underlying windows libraries for
the respective instrument.
mzAPI currently supports Thermo Finnigan .RAW files, ABI .WIFF files, mzML,
and mzURL (web-based data access)

"""

__author__ = 'Jignesh Parikh, James Webber'

import os
import re
import cPickle

#import pythoncom
#from win32com.shell import shell

#import mzTools

MZ_EXT = ('.raw', '.wiff', '.mzml', '.mzml.gz')
MZ_EXT_2 = MZ_EXT + tuple((e + '.lnk') for e in MZ_EXT) # with shortcuts included

MZ_WILDCARD = 'MS Data Files (%s)|%s' % ('; '.join(('*' + e) for e in MZ_EXT),
										 '; '.join(('*' + e) for e in MZ_EXT))

#def follow_link(data_file):
#	link = pythoncom.CoCreateInstance (
#		shell.CLSID_ShellLink,
#		None,
#		pythoncom.CLSCTX_INPROC_SERVER,
#		shell.IID_IShellLink
#	)
#	link.QueryInterface(pythoncom.IID_IPersistFile).Load(data_file)
#
#	# GetPath returns the name and a WIN32_FIND_DATA structure
#	# which we're ignoring. The parameter indicates whether
#	# shortname, UNC or the "raw path" are to be
#	# returned. Bizarrely, the docs indicate that the
#	# flags can be combined.
#
#	data_file, _ = link.GetPath(shell.SLGP_UNCPRIORITY)
#
#	return data_file
#

#class URLDialog(wx.Dialog):
#	def __init__(self, parent):
#		wx.Dialog.__init__(self, parent, -1, "Connect to mzServer")
#
#		gbs = wx.GridBagSizer(10,5)
#
#		gbs.Add( wx.StaticText(self, -1, ("Multiplierz could not find the file locally.\n"
#										  "Connect to an mzServer for remote access?\n"
#										  "(this feature is experimental)"),
#							   style=wx.ALIGN_CENTER),
#				 (0,0), (1,2), flag=wx.EXPAND )
#
#		self.default_ck = wx.CheckBox(self, -1, 'Set as default')
#		gbs.Add( self.default_ck,
#				 (1,0), (1,2), flag=wx.ALIGN_CENTER )
#
#		gbs.Add( wx.Button(self, wx.ID_OK, size=(120,-1)),
#				 (2,0), flag=wx.ALIGN_CENTER )
#
#		gbs.Add( wx.Button(self, wx.ID_CANCEL, 'No', size=(120,-1)),
#				 (2,1), flag=wx.ALIGN_CENTER )
#
#		box = wx.BoxSizer()
#		box.Add(gbs, 0, wx.ALL, 10)
#
#		self.SetSizerAndFit(box)
#
#
#def find_mz_file(local_dir='.', file_name=None, spec_desc=None):
#	'''Takes its best crack at locating an mz_file, using these steps:
#
#	- If 'file_name' is specified, first try to use that path.
#	- If it cannot be found (or is not a full path), look in the local
#	  directory for the file of the same name.
#		- If file_name is not an mz_file type, try appending or
#		  switching the extension.
#		- If file_name is an mzURL, look for the file locally,
#		  then try the URL to make sure it works.
#	- If none of that works, try to use the spectrum description.
#	- If that doesn't work either, return None.
#	'''
#
#	mz_file = None
#
#	import mzURL
#	url_reg = re.compile(r'((http://.+)/files/([^/]+))(?:/scans/.*)?', flags=re.I)
#	check_url = None
#
#	if file_name:
#		url_m = url_reg.match(file_name)
#
#		base = os.path.basename(file_name)
#
#		#for e in ('.raw', '.wiff', '.mzml', '.mzml.gz'):
#		for e in MZ_EXT_2:
#			if file_name.endswith(e) and os.path.exists(file_name):
#				mz_file = file_name
#				break
#			elif file_name.endswith(e) and os.path.exists(os.path.join(local_dir, base)):
#				mz_file = os.path.join(local_dir, base)
#				break
#			elif os.path.exists(file_name + e):
#				mz_file = file_name + e
#				break
#			elif os.path.exists(os.path.join(local_dir, base + e)):
#				mz_file = os.path.join(local_dir, base + e)
#				break
#		else:
#			if url_m:
#				#for e in ('.raw','.wiff','.mzml','.mzml.gz'):
#				for e in MZ_EXT_2:
#					if os.path.exists(os.path.join(local_dir, url_m.group(3) + e)):
#						mz_file = os.path.join(local_dir, url_m.group(3) + e)
#						break
#				else:
#					if mzTools.settings.mzServer == 'always':
#						check_url = True
#					elif mzTools.settings.mzServer == 'ask':
#						with URLDialog(None) as dlg:
#							if dlg.ShowModal() == wx.ID_OK:
#								check_url = True
#								if dlg.default_ck.GetValue():
#									mzTools.settings.mzServer = 'always'
#									mzTools.settings.save()
#							else:
#								check_url = False
#								if dlg.default_ck.GetValue():
#									mzTools.settings.mzServer = 'never'
#									mzTools.settings.save()
#					else:
#						check_url = False
#
#					if check_url and mzURL.check_mzURL(url_m.group(2),
#													   url_m.group(3)):
#						mz_file = url_m.group(1)
#
#
#	if mz_file is None and spec_desc:
#		raw_m = re.match(r'(.+?)\..+\.dta', spec_desc, flags=re.I)
#		wiff_m = re.match(r'File\:\s(.+?)\,', spec_desc, flags=re.I)
#		url_m = url_reg.match(spec_desc)
#
#		if raw_m:
#			mz_file = os.path.join(local_dir, raw_m.group(1) + '.raw')
#			if not os.path.exists(mz_file):
#				if os.path.exists(mz_file+'.lnk'):
#					mz_file += '.lnk'
#				else:
#					mz_file = None
#		elif wiff_m:
#			mz_file = os.path.join(local_dir, wiff_m.group(1))
#			if not os.path.exists(mz_file):
#				if os.path.exists(mz_file+'.lnk'):
#					mz_file += '.lnk'
#				else:
#					mz_file = None
#		elif url_m:
#			#for e in ('.raw','.wiff','.mzml','.mzml.gz'):
#			for e in MZ_EXT_2:
#				if os.path.exists(os.path.join(local_dir, url_m.group(3) + e)):
#					mz_file = os.path.join(local_dir, url_m.group(3) + e)
#					break
#			else:
#				if check_url is None:
#					if mzTools.settings.mzServer == 'always':
#						check_url = True
#					elif mzTools.settings.mzServer == 'ask':
#						with URLDialog(None) as dlg:
#							if dlg.ShowModal() == wx.ID_OK:
#								check_url = True
#								if dlg.default_ck.GetValue():
#									mzTools.settings.mzServer = 'always'
#									mzTools.settings.save()
#							else:
#								check_url = False
#								if dlg.default_ck.GetValue():
#									mzTools.settings.mzServer = 'never'
#									mzTools.settings.save()
#					else:
#						check_url = False
#
#				if check_url and mzURL.check_mzURL(url_m.group(2),
#												   url_m.group(3)):
#					mz_file = url_m.group(1)
#
#	if mz_file is not None and mz_file.lower().endswith('.lnk'):
#		mz_file = follow_link(mz_file)
#
#	return mz_file
#

def make_info_file(data_file, **kwargs):
	"""Generates a text file with mapping for scan time to proprietary scan index

	"""

	if data_file.lower().startswith('http://'):
		raise NotImplementedError('How do you make an info file from a URL?')

	if data_file.lower().endswith('wiff'):
		file_type = 'wiff'
	elif data_file.lower().endswith('raw'):
		file_type = 'raw'
	elif data_file.lower().endswith('mzml'):
		file_type = 'mzml'
	elif data_file.lower().endswith('mzml.gz'):
		file_type = 'mzml'


	if os.path.exists(data_file + '.mzi'):
		os.remove(data_file + '.mzi')

	if file_type is not 'mzml':
		my_file = mzFile(data_file, **kwargs)
		(start_time, stop_time) = my_file.time_range()
		scan_list = my_file.scan_info(start_time, stop_time)
		my_file.close()

		info_list = []
		for (time, mz, scan_name, scan_type, scan_mode) in scan_list:
			my_dict = {'time': time, 'mz': mz, 'scan_name': scan_name, 'scan_type': scan_type, 'scan_mode': scan_mode}
			info_list.append(my_dict)
		info_list = mzInfoFile(info_list)

		#Pickle object

		fh = open(data_file + '.mzi', 'w')
		cPickle.dump(info_list, fh)
		fh.close()
	else:
		import lx.fileReader.mzAPI.mzML
		lx.fileReader.mzAPI.mzML.make_info_file(data_file)


class mzInfoFile(tuple):
	"""Subclass of tuple object for storing mzInfo.

	Each element of the tuple is a dictionary that stores information about each scan
	"""

	def __init__(self, s):
		tuple.__init__(self, s)
		self.index_dict = dict((d["time"], i) for i,d in enumerate(self))

	def field_list(self):
		"""Returns keys for dictionary stored in each list element.

		Assumes all dictionaries have same keys.
		"""

		return self[0].keys()

	def sort_by_field(self, field=None):
		if field:
			return sorted(self, key=lambda e: e[field])
		else:
			return list(self)

	def filter(self, list_key=None, value_list=None, value_range=None, sort_field=None):
		"""All purpose extract data function

		list_key provides the key used to exctract data
		value_list or value_range can be used to provide the values to exctract
		value_list = [val1, val2, val3...]
		value_range = [start_val, stop_val]
		if value_list is provided, range will be ignored

		sort_field option returns the list sorted based on a specified_field
		"""

		#  Extract
		temp_list = self.sort_by_field(field = list_key)
		if value_list != None:
			value_list = set(value_list)
			extracted_list = [i for i in temp_list if i[list_key] in value_list]
		elif value_range != None:
			(start_value, stop_value) = sorted(value_range)
			extracted_list = [i for i in temp_list if start_value <= i[list_key] <= stop_value]
		else:
			extracted_list = temp_list

		if sort_field != None:
			extracted_list.sort(key=lambda i: i[sort_field])

		return extracted_list

	def closest(self, key, value):
		closest_item = self[0]
		if key == "time":
			if value in self.index_dict:
				closest_item = self[self.index_dict[value]]
				return closest_item

		return min((i for i in self), key=lambda e: abs(e[key] - value))


class mzScan(list):
	"""Subclass of list object for custom scan methods

	The mode can be 'p' or 'c' for profile or centroid respectively
	"""

	def __init__(self, s, time, mode='p', mz=0.0, z=0, sn = 0):
		list.__init__(self, s)
		self.time = time
		self.mode = mode
		self.mz = mz
		self.z = z
		self.sn = sn

	def peak(self, mz, tolerance):
		return max([i for m,i in self if abs(m-mz) <= tolerance] or [0])


class mzFile(object):
	"""Base class for access to MS data files"""

	def __init__(self, data_file, **kwargs):
		"""Initializes mzAPI and opens a new file of a specified type

		file_type can be 'raw', 'wiff', 'mzml', or 'mzurl'

		Example:
		>>> dataFile = 'C:\\Documents and Settings\\User\\Desktop\\rawFile.RAW'
		>>> myPeakFile = mzAPI.mzFile(dataFile)

		"""

		if data_file.lower().endswith('.lnk'):
			data_file = self.follow_link(data_file)

		if data_file.lower().startswith('http://'):
			import lx.fileReader.mzAPI.mzURL
			self.__class__ = lx.fileReader.mzAPI.mzURL.mzFile
			lx.fileReader.mzAPI.mzURL.mzFile.__init__(self, data_file, **kwargs)
		elif data_file.lower().endswith('.wiff'):
			import lx.fileReader.lx.fileReader.mzAPI.mzWiff
			self.__class__ = lx.fileReader.mzAPI.mzWiff.mzFile
			lx.fileReader.mzAPI.mzWiff.mzFile.__init__(self, data_file, **kwargs)
		elif data_file.lower().endswith('.raw'):
			import lx.fileReader.mzAPI.raw
			self.__class__ = lx.fileReader.mzAPI.raw.mzFile
			lx.fileReader.mzAPI.raw.mzFile.__init__(self, data_file, **kwargs)
		elif data_file.lower().endswith('.mzml') or data_file.lower().endswith('.mzml.gz'):
			import lx.fileReader.mzAPI.mzML
			self.__class__ = lx.fileReader.mzAPI.mzML.mzFile
			lx.fileReader.mzAPI.mzML.mzFile.__init__(self, data_file, **kwargs)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def close(self):
		"""Closes the open MS data file

		Example:
		>>> myPeakFile.close()

		"""
		raise NotImplementedError('Subclasses must implement this method')

	def scan_list(self, start_time=None, stop_time=None, start_mz=0, stop_mz=99999):
		"""Gets a list of [(time,mz)] in the time and mz range provided

		All full MS scans that fall within the time range are included.
		Only MS/MS scans that fall within the mz range (optional) are included

		Example:
		>>> scan_list = my_peakfile.scan_list(30.0, 35.0, 435.82, 436.00)

		"""

		raise NotImplementedError('Subclasses must implement this method')

	def scan_info(self, start_time, stop_time=0, start_mz=0, stop_mz=99999):
		"""Gets a list of [(time, mz, scan_name, scan_type, scan_mode, polarity, total_ic)] 
		in the time and mz range provided

		scan_name = number for RAW files, (cycle, experiment) for WIFF files.

		All full MS scans that fall within the time range are included.
		Only MS/MS scans that fall within the mz range (optional) are included

		Example:
		>>> scan_info = my_peakfile.scan_info(30.0, 35.0, 435.82, 436.00)


		"""

		raise NotImplementedError('Subclasses must implement this method')


	def scan_time_from_scan_name(self, scan_name):
		"""Gets scan time for wiff (cycle, experiment) tuple or raw scan number

		Example:
		>>> #raw
		>>> scan_time = myPeakFile.scan_time_from_scan_name(2165)
		>>> #wiff
		>>> scan_time = myPeakFile.scan_time_from_scan_name((1252, 3))

		"""

		raise NotImplementedError('Subclasses must implement this method')

	def scan(self, time):
		"""Gets scan based on the specified scan time

		The scan is a list of (mz, intensity, resolution, baseline,
		noise, charge) tuples. Actually only recent versions of the raw
		file format returns all of those. Normally only mz and
		intensity are filled, the others set to zero.

		Example:
		>>> scan = myPeakFile.scan(20.035)

		"""

		raise NotImplementedError('Subclasses must implement this method')

	def xic(self, start_time, stop_time, start_mz, stop_mz, filter=None):
		"""Generates eXtracted Ion Chromatogram (XIC) for given time and mz range

		The function integrates the precursor intensities for given time and mz range.
		The xic is a list of (time,intensity) pairs.

		Example:
		>>> xic = myPeakFile.xic(31.4, 32.4, 435.82, 436.00)

		"""

		raise NotImplementedError('Subclasses must implement this method')

	def time_range(self):
		"""Returns a pair of times corresponding to the first and last scan time

		Example:
		>>> time_range = myPeakFile.time_range()

		"""

		raise NotImplementedError('Subclasses must implement this method')

	def ric(self, *args, **kwargs):
		'''Old name for the xic method'''

		return self.xic(*args, **kwargs)
