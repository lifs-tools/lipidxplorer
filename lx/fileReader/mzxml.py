from lxml import etree as ET

from base64 import b64encode, b64decode, b32decode
from array import array
import sys, re

class Spectrum:
	def __init__(self):
		self.mz_ = array('d')
		self.it_ = array('d')
		self.md_ = {}
	def addPeak(self,mz,it):
		self.mz_.append(mz)
		self.it_.append(it)
	def mz(self,mz=None):
		if mz:
			self.mz_ = array('d',mz)
		else:
			return list(self.mz_)
	def it(self,it=None):
		if it:
			self.it_ = array('d',it)
		else:
			return list(self.it_)
	def peaks(self):
		return len(self.mz_)
	def get(self,key,df=None):
		return self.md_.get(key,df)
	def set(self,key,value):
		self.md_[key] = value
	def metadata(self):
		return self.md_
	def __str__(self):
		s = "BEGIN SPECTRUM\n"
		i = self.md_.items()
		i.sort(key=lambda i: i[0])
		for (k,v) in i:
			s += "%s:\t%s\n"%(k,v)
		for (mz,it) in zip(self.mz_,self.it_):
			s += "%f\t%f\n"%(mz,it)
		s += "END SPECTRUM\n"
		return s

class MzXMLFileReader:

	def __init__(self,f):
		self.fname = f
		self.handle = None
		self.tagre = re.compile(r'^{(.*)}(.*)$')
		self.typemap = {}
		for tag in ('lowMz',
					'highMz',
					'totIonCurrent',
					'basePeakMz',
					'basePeakIntensity',
					'startMz',
					'endMz',
					'precursorMz.precursorIntensity',
					'precursorMz.windowWideness',
					'precursorMz'
					):
			self.typemap[tag] = float
		for tag in ('num',
					'msLevel',
					'peaksCount',
					'scanOrigin.num',
		'msLevel',
					'precursorMz.precursorScanNum',
					'precursorMz.precursorCharge',
					'maldi.laserShootCount',
					'maldi.laserIntensity',
					):
			self.typemap[tag] = int
		for tag in ('retentionTime','maldi.laserFrequency'):
			self.typemap[tag] = lambda s: float(s[2:-1])
		for tag in ('maldi.collisionGas',):
			self.typemap[tag] = lambda s: (s.lower() == 'true' or s != '0')
		for tag in ('polarity',):
			self.typemap[tag] = str
		self.reset()

	def reset(self):
		if self.handle:
			self.handle.close()
			self.handle = None
		self.handle = open(self.fname,'r')
		self.context = []
		self.ns = ''

	def __iter__(self):
		return self.next()

	def extract_scan(self,ele):

		scan = Spectrum()

		for (k,v) in ele.attrib.items():
			scan.set(k,self.typemap.get(k,str)(v))

		if scan.get('num') != None:
			scan.set('scan',scan.get('num'))

		for peakselt in ele.findall(self.ns+'peaks'):

			# wrapper for msconvert file conversion. MSconvert returns empty
			# <peak> contents, while readw puts always a AAAAAAAAAAAA= inside.
			if peakselt.text is None:
				peakselt.text = 'AAAAAAAAAAA='

			peaks = array('f',b64decode(peakselt.text))

			if sys.byteorder != 'big':
				peaks.byteswap()
			scan.mz(peaks[::2])
			scan.it(peaks[1::2])

			break

		for prop in ('scanOrigin','precursorMz','maldi'):
			#print prop,self.ns+prop
			#print list(ele.findall(self.ns+prop))
			for e in ele.findall(self.ns+prop):
				# print e
				if prop in ('precursorMz',):
					scan.set(prop,self.typemap.get(prop,str)(e.text))
				for (k,v) in e.attrib.items():
					t = '%s.%s'%(prop,k)
					scan.set(t,self.typemap.get(t,str)(v))
				break

		for e in ele.findall(self.ns+'nameValue'):
			scan.set(e.attrib['name'],e.attrib['value'])

		for e in ele.findall(self.ns+'comment'):
			scan.set('comment',e.text)
			break

		return scan

	def __next__(self):
		for (event, ele) in ET.iterparse(self.handle,('start','end')):
			# print event,self.context,ele.tag,ele.attrib

			if event == 'start':
				m = self.tagre.search(ele.tag)
				if m:
					self.context.append(m.group(2))
				else:
					self.context.append(ele.tag)
				if self.context in (['mzXML'],['msRun']):
					for (k,v) in ele.attrib.items():
						if k.endswith('schemaLocation'):
							self.ns = '{%s}'%(v.split()[0],)
				continue

			if self.context[-2:] == ['msRun','scan']:

				# ele is now a DOM like object with everything from
				# the highest level scan...

				yield self.extract_scan(ele)

				for e in ele.findall(self.ns+'scan'):
					yield self.extract_scan(e)

				ele.clear()

			self.context.pop()


from .elementtree.SimpleXMLWriter import XMLWriter

class MzXMLFileWriter:
	def __init__(self,s,f):
		self.h = charCounter(open(f,'w'))
		self.w = XMLWriter(self.h)
		self.s = s
		self.scanOffset = {}

	def write(self,**kw):
		mzxmlid = self.w.start('mzXML',
							   {'xmlns':"http://sashimi.sourceforge.net/schema_revision/mzXML_2.2",
								'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance",
								'xsi:schemaLocation':"http://sashimi.sourceforge.net/schema_revision/mzXML_2.2 http://sashimi.sourceforge.net/schema_revision/mzXML_2.2/mzXML_idx_2.2.xsd"
								})

		count = 0;
		for s in self.s:
			count += 1
		self.s.reset()

		self.w.data('\n  ');
		self.w.start('msRun',scanCount=str(count))
##		 self.w.data('\n	');
##		 self.w.start('msInstrument')
##		 self.w.data('\n	  ');
##		 self.w.start('msManufacturer',category='msManufacturer',value=""); self.w.end();
##		 self.w.data('\n	  ');
##		 self.w.start('msModel',category='msModel',value=""); self.w.end();
##		 self.w.data('\n	  ');
##		 self.w.start('msIonisation',category='msIonisation',value=""); self.w.end();
##		 self.w.data('\n	  ');
##		 self.w.start('msMassAnalyzer',category='msMassAnalyzer',value=""); self.w.end();
##		 self.w.data('\n	  ');
##		 self.w.start('msDetector',category='msDetector',value=""); self.w.end();
##		 self.w.data('\n	  ');
##		 self.w.start('software',type='acquisition',name="",version=""); self.w.end();
##		 self.w.data('\n	');
##		 self.w.end()
##		 self.w.data('\n	');
##		 self.w.start('dataProcessing')
##		 self.w.data('\n	  ');
##		 self.w.start('software',conversion='PyMsIO',version=""); self.w.end();
##		 self.w.data('\n	');
##		 self.w.end()

		lastscanlevel = [ 0 ]
		scannum = 0;
		for s in self.s:
			scan_metadata = dict(s.metadata())

			while scan_metadata['msLevel'] <= lastscanlevel[-1]:
				self.w.data('\n	');
				self.w.end('scan')
				lastscanlevel.pop()

			lastscanlevel.append(scan_metadata['msLevel'])
			attrib = {}
			for tag in ('lowMz',
						'highMz',
						'totIonCurrent',
						'basePeakMz',
						'basePeakIntensity',
						'startMz',
						'endMz',
						'msLevel',
						'peaksCount',
						'polarity',
						):
				if tag in scan_metadata:
					attrib[tag] = str(scan_metadata[tag])
					del scan_metadata[tag]
			scannum += 1
			attrib['num'] = str(scannum)
			del scan_metadata['num']
			del scan_metadata['scan']
			del scan_metadata['ordinal']

			if 'retentionTime' in scan_metadata:
				attrib['retentionTime'] = "PT%fS"%(scan_metadata['retentionTime'])
				del scan_metadata['retentionTime']

			self.w.data('\n	');
			self.scanOffset[scannum] = self.h.chars()+5
			self.w.start('scan',attrib)

			if 'precursorMz' in scan_metadata:
				attrib = {}
				for tag in ('precursorMz.precursorIntensity',
							'precursorMz.windowWideness',
							'precursorMz.precursorScanNum',
							'precursorMz.precursorCharge'):
				   if tag in scan_metadata:
					   attrib[tag[len('precursorMz.'):]] = str(scan_metadata[tag])
					   del scan_metadata[tag]
				self.w.data('\n	  ');
				self.w.element('precursorMz',str(scan_metadata['precursorMz']),attrib)
				del scan_metadata['precursorMz']

			if 'scanOrigin.num' in scan_metadata:
				attrib = {}
				for tag in ('scanOrigin.num',
							'scanOrigin.parentFileID'):
				   if tag in scan_metadata:
					   attrib[tag[len('scanOrigin.'):]] = str(scan_metadata[tag])
					   del scan_metadata[tag]
				self.w.data('\n	  ');
				self.w.element('scanOrigin',attrib=attrib)

			self.w.data('\n	  ');
			self.w.start('peaks',
						 precision="32",
						 byteOrder="network",
						 pairOrder="m/z-int")
			peaks = array('f');
			for (mz,it) in zip(s.mz(),s.it()):
				peaks.append(mz)
				peaks.append(it)
			if sys.byteorder != 'big':
				peaks.byteswap()
			self.w.data(b64encode(peaks.tostring()))
			self.w.end()

			for (k,v) in scan_metadata.items():
				self.w.data('\n	  ');
				self.w.element('nameValue',name=k,value=str(v))

			# self.w.end()

		while lastscanlevel[-1] != 0:
			self.w.data('\n	');
			self.w.end('scan')
			lastscanlevel.pop()

		self.w.data('\n  ');
		self.w.end('msRun')
		self.w.data('\n  ');
		indexOffset = self.h.chars()+3
		self.w.start('index',name='scan')
		for i in sorted(self.scanOffset.keys()):
			self.w.data('\n	');
			self.w.element('offset',str(self.scanOffset[i]),id=str(i))
		self.w.data('\n  ');
		self.w.end()
		self.w.data('\n  ');
		self.w.element('indexOffset',str(indexOffset))
		self.w.data('\n');
		self.w.close(mzxmlid)
		self.w.data('\n');

class PrecursorSort:
	def __init__(self,input,asc=True):
		self.asc = asc
		self.input = input

	def __iter__(self):
		return next(self)

	def __next__(self):
		spectra = list(self.input)
		spectra.sort(key = lambda s: s.get('precursorMz',None),reverse=(not self.asc))
		for s in spectra:
			yield s

