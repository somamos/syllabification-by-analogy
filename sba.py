# Syllabification By Analogy
# Implements the method described in Marchand & Damper's 
# "Can syllabification improve pronunciation by analogy of English?

from lattice import Lattice, ERRORS

class SyllabifierByAnalogy:
	def __init__(self, path="Preprocessing/Out/output.txt", verbose=False):
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			# Determine syllable breaks from each word's encoding.
			# R1: [<>] denotes [<|>]
			# R2: [<digit] denotes [<|digit]
			# R3: [digit>] denotes [digit|>]
			# R4: [digit digit] denotes [digit|digit]
			boundaries = set(['<>', '<0', '<1', '<2', '0>', '1>', '2>', \
				'00', '01', '02', '10', '11', '12', '20', '21', '22'])
			for line in f:
				junctured_key = '' # Every juncture will be a *.
				junctured_entry = '' # Junctures will be * or |.
				line = line.split()
				letters = line[0]
				encoding = line[2]
				if len(letters) != len(encoding):
					print('Error: mapping between {} and {} is not 1-to-1.'.format(letters, encoding))
					continue
				# Iterate up to the second-to-last character (we will look ahead by 1 index)
				for i in range(len(letters) - 1):
					# Add char before potential boundary.
					junctured_key += letters[i]
					junctured_entry += letters[i]
					# Add juncture POSSIBILITY to key.
					junctured_key += '*'
					# Determine whether a syllable boundary actually exists.
					potential_boundary = encoding[i] + encoding[i + 1]
					if potential_boundary in boundaries:
						junctured_entry += '|'
					else:
						junctured_entry += '*'
				# Add the last letter.
				junctured_key += letters[-1]
				junctured_entry += letters[-1]
				# Add entry.
				self.lexical_database[junctured_key] = junctured_entry
				# Precalculate substrings.
				self.substring_database[junctured_key] = [[junctured_key[i:j] for j in range(i, len(junctured_key) + 1) \
					if j - i > 1] for i in range(0, len(junctured_key) - 1)]
				if verbose:
					print('{}\n{}\n{}\n\n'.format(junctured_key, junctured_entry, self.substring_database[junctured_key]))



sba = SyllabifierByAnalogy(verbose=True)