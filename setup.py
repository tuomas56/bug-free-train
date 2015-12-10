from setuptools import setup, find_packages
setup(name="game", 
	package_dir={'':'src'},
	version="0.1",
	packages=find_packages('src'),
	scripts=['src/play'],
	install_requires=[
		'noise'
	])
