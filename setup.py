import setuptools

# Import version from the package
from grouper import __version__

setuptools.setup(
	name='grouper',
	version=__version__,
	description='Administer Grouper groups.',
	url='https://github.com/ryanlovett/grouper',
	author='Ryan Lovett',
	author_email='rylo@berkeley.edu',
	packages=setuptools.find_packages(),
	install_requires=[
	  'requests'
	],
	extras_require={
		'dev': [
			'unittest-xml-reporting',  # For CI/CD XML test reports
		],
		'test': [
			'pytest>=6.0',
			'pytest-cov',
			'coverage',  # For test coverage reports
		],
	},
    entry_points={
        'console_scripts': [
            'grouper = grouper.__main__:main',
        ],
    },
	python_requires='>=3.6',
	classifiers=[
		'Development Status :: 4 - Beta',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11',
		'Programming Language :: Python :: 3.12',
	],
)
