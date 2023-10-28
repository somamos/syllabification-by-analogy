# A python implementation of Damper and Marchand's "Aligning Text and Phonemes 
#       for Speech Technology Applications Using an EM-Like Algorithm"

class Aligner:
	class Matrix:
		class Cell:
			def __init__(self, letter, phoneme, val):
				self.letter = letter
				self.phoneme = phoneme
				self.val = val


		def get_by_index(self, i, j):
			return self.A[ i ][ j ].val
		def set_by_index(self, i, j, val):
			self.A[ i ][ j ].val = val
		def iterate_by_index(self, i, j):
			self.A[ i ][ j ].iterate()

		def get(self, l, p):
			return self.A[ self.L.index(l) ][ self.P.index(p) ].val
		def set(self, l, p, val):
			self.A[ self.L.index(l) ][ self.P.index(p) ] = val
		def iterate(self, l, p):
			self.A[ self.L.index(l) ][ self.P.index(p) ].val += 1

		def __init__(self, rows, cols, init = None):
			# Map all phonemes and letters to indices.
			self.L = rows
			self.P = cols
			self.A = [] # Populate association matrix with initial values.
			for i in self.L:
				row = []
				for j in self.P:
					val = 0 if init is None else init.get(i, j)
					row.append(self.Cell(i, j, val))
				self.A.append(row)

		def __str__(self):
			s = ' '
			s += ''.join(['{:>8}'.format(p) for p in self.P]) # Print col labels.
			s += '\n'
			for i, row in enumerate(self.A):
				s += '{}'.format(self.L[i]) # Print row labels.
				for cell in row:
					s += '{:>8}'.format(cell.val) # Print individual cells.
				s += '\n'
			return s


	# Letters will map to row indices -- Phonemes, column indices -- of a
	# so-called association matrix. It scores the likelihood of pairings.
	def __init__(self, alphabet, phonemes, wordlist):
		self.LETTER_PAD = '#'
		self.PHONEME_PAD = '$'
		
		# Given two lists of characters and an optional matrix of starting values;
		# Return the matrix, A, as well as two dicts, L and P,
		# which map single characters to indices in A.


		# Add characters to represent the borders of words.
		alphabet.append(self.LETTER_PAD)
		phonemes.append(self.PHONEME_PAD)
		# A's values will be counts.
		A = self.Matrix(alphabet, phonemes)

		# Naive pass, A^0. We're counting every instance a letter and phoneme
		# exist within the same word.
		for word in wordlist:
			for letter in word.letters:
				for phoneme in word.phonemes:
					A.iterate(letter, phoneme)

		print(A)

		# Begin alignment.
		def score(word):
			# Pad.
			padded_letters = self.LETTER_PAD + word.letters + self.LETTER_PAD
			padded_phones = self.PHONEME_PAD + word.phonemes + self.PHONEME_PAD

			# B's values will be initial scores.
			B = self.Matrix(padded_letters, padded_phones, A)
			print(B)
			print('\n\n')
			# C's values, accumulated scores.
			C = self.Matrix(padded_letters, padded_phones)
			# D's values, references to "previous Cells."
			D = self.Matrix(padded_letters, padded_phones)
			# Iterate through C, adding max of prev vals and pointing D towards it.
			for i, ch in enumerate(padded_letters):
				for j, ph in enumerate(padded_phones):
					# Beginning cases.
					if i == 0 or j == 0:
						continue
					maximum = 0
					curr = 0
					curr_coord = None
					# Either cell above,
					o1 = C.get_by_index(i - 1, j)
					# cell to the left,
					o2 = C.get_by_index(i, j - 1)
					# or cell to the top left plus current.
					o3 = C.get_by_index(i - 1, j - 1) + B.get_by_index(i, j)
					
					best = max((o1, o2, o3))

					C.set_by_index(i, j, best)
					if best == o3:
						D.set_by_index(i, j, '\\')
					elif best == o2:
						D.set_by_index(i, j, '->')
					elif best == o1:
						D.set_by_index(i, j, ('|'))
			print(C)
			print('\n\n')
			print(D)
			print('\n\n\n\n\n')

		print('Printing the word {}'.format(wordlist[0].letters))
		for i in range (100):
			score(wordlist[i])





















