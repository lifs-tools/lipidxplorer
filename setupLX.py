from distutils.core import setup

setup(
	name = "LipidXplorer",
	version = "1.2.8",
	author = "Ronny Herzog, Fadi Al Machot, Jacobo Miranda Ackerman",
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
	long_description = "..."
)
