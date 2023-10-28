# A python implementation of "Aligning Text and Phonemes 
# for Speech Technology Applications Using an EM-Like Algorithm"
# by Damper and Marchand.

class Aligner:
	def __init__(self, alphabet, phonemes, wordlist):
		# Represent the borders of words.
		alphabet.append('#')
		phonemes.append('$')
		A = {} # Association matrix.
		# Naive pass, A^0.
		for word in wordlist:
			for letter in word.letters:
				for phoneme in word.phonemes:
					A[letter + phoneme] = A.get(letter + phoneme, 0) + 1
		print(A)