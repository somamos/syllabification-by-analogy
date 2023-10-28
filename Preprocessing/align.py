# A python implementation of Damper and Marchand's "Aligning Text and Phonemes 
#       for Speech Technology Applications Using an EM-Like Algorithm"

class Aligner:

	class Matrix:

		class Cell:
			def iterate(self):
				self.val += 1
			def __init__(self, letter, phoneme, val):
				self.letter = letter
				self.phoneme = phoneme
				self.val = val

		def get(self, i, j):
			return self.A[ self.L[i] ][ self.P[j] ].val

		def set(self, i, j, val):
			self.A[ self.L[i] ][ self.P[j] ] = val

		def iterate(self, i, j):
			self.A[ self.L[i] ][ self.P[j] ].iterate()

		def __init__(self, rows, cols, init = None):
			# Map all phonemes and letters to indices.
			self.L = {}
			self.P = {}
			for index, letter in enumerate(rows):
				self.L[letter] = index
			for index, phoneme in enumerate(cols):
				self.P[phoneme] = index
			self.A = [] # Populate association matrix with initial values.
			for i in self.L.keys():
				row = []
				for j in self.P.keys():
					val = 0 if init is None else init.get(i, j)
					row.append(self.Cell(i, j, 0))
				self.A.append(row)

		def __str__(self):
			s = ''
			for row in self.A:
				for cell in row:
					s += '{}{}: {}, '.format(cell.letter, cell.phoneme, cell.val)
				s += '\n'
			return s


	# Letters will map to row indices -- Phonemes, column indices -- of a
	# so-called association matrix. It scores the likelihood of pairings.
	def __init__(self, alphabet, phonemes, wordlist):
		# Given two lists of characters and an optional matrix of starting values;
		# Return the matrix, A, as well as two dicts, L and P,
		# which map single characters to indices in A.


		# Add characters to represent the borders of words.
		alphabet.append('#')
		phonemes.append('$')
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
			# B's values, initial scores.
			B = self.Matrix(word.letters, word.phonemes, A)
			# C's values will be accumulated scores.
			C = self.Matrix(word.letters, word.phonemes)
			# D's values will point to previous Cells.
			D = self.Matrix(word.letters, word.phonemes)



