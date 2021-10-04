from distutils.core import setup

setup(
	name = "LipidXplorer",
	version = "1.2.7",
	author = "Ronny Herzog",
	maintainer= = "Jacobo Miranda",
	author_email = "mirandaa@mpi-cbg.de",
	url = "https://wiki.mpi-cbg.de/wiki/lipidx/index.php/Main_Page",
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
