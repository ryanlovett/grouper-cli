import setuptools

setuptools.setup(
	name='grouper',
	version='0.1',
	description='Administer Grouper groups.',
	url='https://github.com/ryanlovett/grouper',
	author='Ryan Lovett',
	author_email='rylo@berkeley.edu',
	packages=setuptools.find_packages(),
	install_requires=[
	  'requests'
	],
    entry_points={
        'console_scripts': [
            'grouper = grouper.__main__:main',
        ],
    },

)
