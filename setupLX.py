from distutils.core import setup

setup(
	name = "LipidXplorer",
	version = "1.2.8_dev",
	author = "Ronny Herzog, Jacobo Miranda Ackerman, Fadi Al Machot, Nils Hoffmann",
	author_email = "lifs-support@isas.de",
	url = "https://lifs.isas.de/wiki/index.php/Main_Page",
	packages = ['lx'],# 'mfql'],
	package_data = {'lx' : ['lx/*']},#, 'mfql' : ['mfql/*']},
	windows = [
		{
			"scripts": "Lipidxplorer.py",
			"icon_resources": [(1, "lx/stuff/lipidx_ico.ico")]
		}],
	scripts = ['LipidXplorer.py'],
	long_description = "LipidXplorer is a software that is designed to support bottom-up and top-down shotgun lipidomics experiments performed "+
					   "on all types of tandem mass spectrometers. Lipid identification does not rely on a database resource of reference "+
					   "or simulated mass spectra but uses user-defined molecular fragment queries. It supports accurate, isotope-corrected "+
					   "quantification based on the identified MS1 or MS2 level fragments."
)
