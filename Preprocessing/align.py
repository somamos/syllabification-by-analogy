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
			return self.A[ self.L.index(i) ][ self.P.index(j) ].val

		def set(self, i, j, val):
			self.A[ self.L.index(i) ][ self.P.index(j) ] = val

		def iterate(self, i, j):
			self.A[ self.L.index(i) ][ self.P.index(j) ].iterate()

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
			s = ''
			for row in self.A:
				for cell in row:
					s += '{}{}: {}, '.format(cell.letter, cell.phoneme, cell.val)
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
			# C's values, accumulated scores.
			C = self.Matrix(padded_letters, padded_phones)
			# D's values, references to "previous Cells."
			D = self.Matrix(padded_letters, padded_phones)

		print('Printing the word {}'.format(wordlist[0].letters))
		for i in range (100):
			score(wordlist[i])





















