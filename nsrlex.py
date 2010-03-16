#!/usr/bin/python
# nsrlex.py
"""
NSRL hashsets extractor 

Extracts known-good and known-bad entries from NSRL signatures
files based on ProductCodes matching any NSRLProd files
entry labeled 'Hacker Tool'

This tool is based on nsrlext.pl from Tony Rodrigues <dartagnham at gmail dot com>

@author Jan Seidl <jan.seidl@heavyworks.net>
@version 1.0
@license http://www.opensource.org/licenses/gpl-3.0.html GNU Public License
"""


import sys, getopt
import os.path

# Variable initialization
sScriptName = sys.argv[0]

def main():
	"""
	Main function

	@uses	index_hacker_tool_entries
	@uses	filter_entries
	@uses	write_output
	@uses	display_summary
	@uses	check_file
	"""

	# Variable initialization
	sNSRLFile = None
	sProdFile = None
	sKnownGoodOutputFile = None
	sKnownBadOutputFile = None
	bShowSummary = False

	# Get Options from command-line
	# Getopt style with both short and long names
	try:
		aOpts, aArgs = getopt.getopt(sys.argv[1:], "shn:p:g:b:", ["show-summary","help", "nsrl-file=","prod-file=","output-good-file=","output-bad-file="])
	except getopt.GetoptError as oErr:
		# Or fail gracefully:
		sErr = str(oErr)
		raise_error(sErr)

	# Process the getopt parameters
	for sOption, sValue in aOpts:
		if sOption in ('-h','--help'):
			usage()
			sys.exit()
		elif sOption in ('-n','--nsrl-file'):
			sNSRLFile = sValue
		elif sOption in ('-p','--prod-file'):
			sProdFile = sValue
		elif sOption in ('-g','--output-good-file'):
			sKnownGoodOutputFile = sValue
		elif sOption in ('-b','--output-bad-file'):
			sKnownBadOutputFile = sValue
		elif sOption in ('-s','--show-summary'):
			bShowSummary = True
		else:
			assert False, "unhandled option"

	# Check required files
	if not check_file(sNSRLFile):
		raise_error('NSRL Signature file (-n|--nsrl-file) is required and must contain valid files.')

	if not check_file(sProdFile):
		raise_error('NSRL Prod file (-p|--prod-file) is required and must contain valid files.')

	if not sKnownGoodOutputFile and \
	   not sKnownBadOutputFile:
		raise_error('You must define at least one output file.')

	# index Hacker Tool entries
	aHackerTools = index_hacker_tool_entries(sProdFile)

	# Filter entries into known-good and known-bad
	aEntries = filter_entries(sNSRLFile, aHackerTools, sKnownGoodOutputFile, sKnownBadOutputFile)

	# Write entries to respective output files, if supplied
	write_output(aEntries, sKnownGoodOutputFile, sKnownBadOutputFile)

	if bShowSummary:
		show_summary(aEntries)	
	
	return 0

def index_hacker_tool_entries(sNSRLProdEntries):	
	"""
	Returns unique ProductCodes from supplied NSRLProd files.

	@usedby	main()
	
	@param	string	sNSRLProdEntries	Comma-separated paths for NSRLProd files

	@return	list	List (array) of ProductCodes
	"""

	aNSRLProdFiles = sNSRLProdEntries.split(',')
	aHackerTools = []

	for sFile in aNSRLProdFiles:
		try:
			oNSRLProdFile = open(sFile,'r')

			for sNSRLProdEntry in oNSRLProdFile:

				aNSRLProdEntry = sNSRLProdEntry.split(',')

				if aNSRLProdEntry[6].find('Hacker Tool') != -1 and \
				not in_array(aNSRLProdEntry[0], aHackerTools):
					aHackerTools.append(aNSRLProdEntry[0])
				
			oNSRLProdFile.close()

		except IOError:
			raise_error('Could not read NSRL Prod file '+sFile+'.')

	return aHackerTools

def filter_entries(sNSRLFileEntries, aHackerTools, sKnownGoodOutputFile, sKnownBadOutputFile):
	"""
	Returns the entries split into good and bad based on
	the supplied hacker tools ProductNumbers.

	KnownGood and KnownBad output files are only supplied to skip
	processing (and thus allocating memory) for them if they
	are NoneType (not specified).

	@usedby	main()

	@param	string	sNSRLFileEntries		Comma-separated paths for NSRLFiles
	@param	list	aHackerTools			List of ProductCodes marked as 'Hacker Tool'
	@param	string	sKnownGoodOutputFile	Path for known-good entries output file
	@param	string	sKnownBadOutputFile		Path for known-bad entries output file

	@return	dictionary	Dictionary with entries split between 'good' and 'bad' keys for known-good and known-bad entries respectively
 	"""

	aNSRLFiles = sNSRLFileEntries.split(',')

	aEntries = {'good': [], 'bad': []}

	for sFile in aNSRLFiles:
		try:
			oNSRLFile = open(sFile,'r')

			for sNSRLEntry in oNSRLFile:
				aNSRLLine = sNSRLEntry.split(',')
			
				if not in_array(aNSRLLine[5],aHackerTools) and \
					sKnownGoodOutputFile:

					aEntries['good'].append(sNSRLEntry)

				elif sKnownBadOutputFile:
					aEntries['bad'].append(sNSRLEntry)

			oNSRLFile.close()

		except IOError:
			raise_error('Could not read NSRL Signature file '+sFile+'.')

	return aEntries

def write_output(aEntries, sKnownGoodOutputFile, sKnownBadOutputFile):
	"""
	Write entries to their corresponding output file, if supplied.

	@usedby	main()

	@param	dictionary	aEntries	Entries sorted between 'good' and 'bad'
	@param	string	sKnownGoodOutputFile	Path for known-good entries output file
	@param	string	sKnownBadOutputFile		Path for known-bad entries output file

	@return	void
	"""

	# Open known-good output file for writing
	# and write down the entries
	if sKnownGoodOutputFile:
		try:
			oKnownGoodOutputFile = open(sKnownGoodOutputFile, 'w')

			for sEntry in aEntries['good']:
				oKnownGoodOutputFile.write(sEntry)

			oKnownGoodOutputFile.close()
		except IOError:
			raise_error('Could not open known-good output file ('+sKnownGoodOutputFile+') for writing')

	# Open known-bad output file for writing
	# and write down the entries
	if sKnownBadOutputFile:
		try:
			oKnownBadOutputFile = open(sKnownBadOutputFile, 'w')
			
			for sEntry in aEntries['bad']:
				oKnownBadOutputFile.write(sEntry)

			oKnownBadOutputFile.close()

		except IOError:
			raise_error('Could not open known-bad output file ('+sKnownBadOutputFile+') for writing')

def show_summary(aEntries):
	"""
	Show extraction summary.
	Displays extraction count and percentage for each hashset

	@usedby	main()

	@param	dictionary	aEntries	Entries sorted between 'good' and 'bad'

	@return void
	"""

	tool_header()

	# Lengths
	iKnownGoodLength = len(aEntries['good'])
	iKnownBadLength = len(aEntries['bad'])
	iTotalLength = (iKnownGoodLength+iKnownBadLength)

	# Percentages
	fKnownGoodPercent = (1.0*iKnownGoodLength/iTotalLength)*100
	fKnownBadPercent = (1.0*iKnownBadLength/iTotalLength)*100

	print "Extraction summary:"

	print "\tKnown-Good:\t"+str(iKnownGoodLength)+"\t("+str(fKnownGoodPercent)+"%)"
	print "\tKnown-Bad:\t"+str(iKnownBadLength)+"\t("+str(fKnownBadPercent)+"%)"
	print

def check_file(sFileString):
	"""
	Checks if file is valid

	@param	string	sFileString	Path to file

	@return	boolean	True if file exists, False otherwise
	"""

	# Check if string has actually any value
	if not sFileString:
		return False

	aFiles = sFileString.split(',')

	# Test if is actually a file
	for sFile in aFiles:
		if not os.path.isfile(sFile):
			return False

	# If it doesnt fall in any of
	# our filters, proceed
	return True

def raise_error(sErrorString):
	"""
	Writes error to stderr and exits with 2 error code
	Echoes usage()

	@uses	usage()

	@param	string	sErrorString	Error string to be echoed to stderr

	@return	void
	"""
	# print error to stderr
	sys.stderr.write(sScriptName+' error: '+sErrorString+'\n\n')
	# help information to stdout
	usage();
	# exit with failure status
	sys.exit(2)

def in_array(sNeedle, aHaystack):
	"""
	Check if item (needle) is in list (haystack)

	@param	string	sNeedle		Item to be found
	@param	mixed	aHaystack	List, Tuple or Dictionary to be analyzed

	@return	boolean	True if index is found, False otherwise
	"""
	try:
		i = aHaystack.index(sNeedle)
	except ValueError:
		i = -1 # no match

	return False if i == -1 else True

def tool_header():
	print "NSRL Extractor"
	print "Extracts known-good and known-bad hashsets from NSRL file based on NSRL Prod file classification"
	print "Jan Seidl"
	print "jan.seidl at heavyworks dot net"
	print "-------------------------------------------------------------------------------------------------"
	print

def usage():
	"""
	Display program usage getopt flags both in short and long form

	@usedby	main()
	@usedby	raise_error()

	@return	void
	"""
	print "usage:"
	print "\t-n, --nsrl-file:\tThe NSRL signature files comma separated."
	print "\t-p, --prod-file:\tThe NSRL Prod files comma separated."
	print "\t-g, --output-good-file:\tThe file which known-good hashsets will be saved"
	print "\t-b, --output-bad-file:\tThe file which known-bad hashsets will be saved"

if __name__ == "__main__":
    sys.exit(main())
