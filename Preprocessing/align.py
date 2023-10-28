# A python implementation of "Aligning Text and Phonemes 
# for Speech Technology Applications Using an EM-Like Algorithm"
# by Damper and Marchand.

class Aligner:

	class Cell:
		def __init__(self, letter, phoneme, count):
			self.letter = letter
			self.phoneme = phoneme
			self.count = count

	def __init__(self, alphabet, phonemes, wordlist):
		# Add characters to represent the borders of words.
		alphabet.append('#')
		phonemes.append('$')


		# Map all phonemes and letters to indices.
		L = {}
		P = {}
		for index, letter in enumerate(alphabet):
			L[letter] = index
		for index, phoneme in enumerate(phonemes):
			P[phoneme] = index
		A = [] # Populate association matrix with initial values.
		for i in L.keys():
			row = []
			for j in P.keys():
				row.append(self.Cell(i, j, 0))
			A.append(row)


		# Naive pass, A^0.
		for word in wordlist:
			for letter in word.letters:
				for phoneme in word.phonemes:
					A[L[letter]][P[phoneme]].count += 1
		for row in A:
			for cell in row:
				print('{}{}: {}, '.format(cell.letter, cell.phoneme, cell.count), end='')
			print('\n')

			