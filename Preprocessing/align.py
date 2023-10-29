# A python implementation of Damper and Marchand's "Aligning Text and Phonemes 
#       for Speech Technology Applications Using an EM-Like Algorithm"

class Aligner:
	class Matrix:
		class Cell:
			def __init__(self, letter, phoneme, val):
				self.letter = letter
				self.phoneme = phoneme
				self.val = val
		def letter_at(self, i, j):
			return self.A[ i ][ j ].letter
		def phoneme_at(self, i, j):
			return self.A[ i ][ j ].phoneme
		def get_by_index(self, i, j):
			return self.A[ i ][ j ].val
		def set_by_index(self, i, j, val):
			self.A[ i ][ j ].val = val
		def iterate_by_index(self, i, j):
			self.A[ i ][ j ].val += 1

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
				for j, cell in enumerate(row):
					# Special print needed for None
					if cell.val is None:
						s += '{:>8}'.format('X') # Print individual cells.
						continue
					# Regular case
					elif type(cell.val) is not tuple:
						s += '{:>8}'.format(cell.val) # Print individual cells.
						continue
					# Special print needed for tuples
					# The tuple represents coords of a neighboring cell. The difference
					# between that coord and current coord will determine which
					# symbol to print.
					to_i, to_j = cell.val
					diff_i = to_i - i
					diff_j = to_j - j
					arrow = ''
					if diff_i == -1 and diff_j == 0:
						arrow = '|'	# Arrow pointing up
					elif diff_i == 0 and diff_j == -1:
						arrow = '->' # Arrow pointing right
					elif diff_i == -1 and diff_j == -1:
						arrow = '\\' # Arrow pointing bottom right
					elif diff_i == 0 and diff_j == 0:
						arrow = 'X' # Top left most.
					else:
						print('Starting at ({}, {}) and going to ({}, {}). Diff: {}, {}' \
							.format(i, j, to_i, to_j, diff_i, diff_j))
						print('Something is very wrong.')
						exit()
					s += '{:>8}'.format(arrow)

				s += '\n'
			return s


	# Letters will map to row indices -- Phonemes, column indices -- of a
	# so-called association matrix. It scores the likelihood of pairings.
	def __init__(self, alphabet, phonemes, wordlist):
		# We stop iterating when cumulative_score stops changing.
		cumulative_score = 0
		# Add characters to represent the borders of words.
		self.LETTER_PAD = '#'
		self.PHONEME_PAD = '$'
		alphabet.append(self.LETTER_PAD)
		phonemes.append(self.PHONEME_PAD)
		
		# Given two lists of characters and an optional matrix of starting values;
		# Return the matrix, A, as well as two lists, L and P,
		# which map single characters to indices in A.

		# A's values will be counts.
		A = self.Matrix(alphabet, phonemes)

		# Naive pass, A^0. We're counting every instance a letter and phoneme
		# exist within the same word.
		for word in wordlist:
			for letter in word.letters:
				for phoneme in word.phonemes:
					A.iterate(letter, phoneme)
					cumulative_score += 1
			# Pad.
			word.letters = self.LETTER_PAD + word.letters + self.LETTER_PAD
			word.phonemes = self.PHONEME_PAD + word.phonemes + self.PHONEME_PAD					
		# Print A^0.
		print(A)

		# Begin alignment.
		def score(word):
			score = 0
			# Bear in mind, the words and phonemes by this point have been padded.
			# B's values will be initial scores.
			B = self.Matrix(word.letters, word.phonemes, A)
			#print(B)
			#print('\n\n')
			# C's values, accumulated scores.
			C = self.Matrix(word.letters, word.phonemes)
			# D's values, arrows pointing to either the top (|), left(->), or top left (\) cell.
			D = self.Matrix(word.letters, word.phonemes)
			# Iterate through C, adding max of prev vals and pointing D towards it.
			for i, ch in enumerate(word.letters):
				for j, ph in enumerate(word.phonemes):
					# Beginning cases.
					if i == 0 and j == 0:
						# Set D's first index.
						D.set_by_index(0, 0, None)
						continue
					elif i == 0 or j == 0: # Topmost and leftmost columns are zeroes all the way through.
						# j is 0, point to left.
						D.set_by_index(i, j, (max(i - 1, 0), max(j - 1, 0)))
						continue
					# Three candidates:
					# the cell above,
					o1 = C.get_by_index(i - 1, j)
					# the cell to the left,
					o2 = 0 #C.get_by_index(i, j - 1) # prevent the null letter.
					# or the cell to the top left plus current.
					o3 = C.get_by_index(i - 1, j - 1) + B.get_by_index(i, j)
					
					best = max((o1, o2, o3))

					C.set_by_index(i, j, best)
					if best == o3:
						D.set_by_index(i, j, (i - 1, j - 1))
					elif best == o2:
						D.set_by_index(i, j, (i, j - 1))
					elif best == o1:
						D.set_by_index(i, j, (i - 1, j))
			#print(C)
			#print('\n\n')
			#print(D)
			#print('\n\n\n\n\n')
			i = len(word.letters) - 1
			j = len(word.phonemes) - 1
			# Save score.
			score = C.get_by_index(i, j)
			# Now trace backwards, adding null phonemes as necessary.
			cell = D.get_by_index(i, j)
			#print('WORD: {}'.format(word.letters))
			while cell != None:
				#print('{}: {}'.format(D.letter_at(i, j), D.phoneme_at(i, j)))
				to_i, to_j = D.get_by_index(i, j)

				diff_i = to_i - i
				diff_j = to_j - j
				if diff_i == -1 and diff_j == 0:
					# Matrix D has an "arrow pointing down" at this cell.
					# Therefore, inject a null phoneme.
					# Because we're moving right to left, we can inject this in place.
					word.phonemes = word.phonemes[:i] + '-' + word.phonemes[i:]
				elif diff_i == -1 and diff_j == -1:
					# Iterate count of that letter-phoneme pair.
					A_.iterate(D.letter_at(i, j), D.phoneme_at(i, j))
				elif diff_i == 0 and diff_j == -1 and i == 0:
					# We should only be going left on the very last, hence the third condition.
					# Also, let's, like, not count these moments.
					break
				else:
					print('Starting at ({}, {}) and going to ({}, {}). Diff: {}, {}' \
						.format(i, j, to_i, to_j, diff_i, diff_j))
					print('The valid options have been exhausted, but none applied.')
					exit()
				#print('Coords {}, {} turning to coords {}, {}'.format(i, j, x, y))
				# Move to other coords.
				cell = D.get_by_index(to_i, to_j)
				i = to_i
				j = to_j

			return word, score

		# A new, blank copy to update our counts.
		A_ = self.Matrix(alphabet, phonemes)
		# Reset the score.
		prev_cumulative_score = cumulative_score
		cumulative_score = 0
		# We only print these changes after convergence.
		candidate_wordlist = wordlist.copy()
		total = len(candidate_wordlist)
		curr = 0
		iteration = 1
		for word in candidate_wordlist:
			# Score each word, adding score to total.
			word, score_ = score(word)
			cumulative_score += score_
			curr += 1
			if curr % 5000 == 0:
				print('ITERATION {}: Scored {}/{} words.'.format(iteration, curr, total))
		# TODO: Get this to work with a deep copy. 
		# Without a deep copy, I believe I'll keep erroneously adding dashes?
		# Or maybe I can just check for whether or not a dash already exists at that location...
		# Maybe I can construct the string naively from scratch, even?
		print('Previous score: {}. Current score: {}'.format(prev_cumulative_score, cumulative_score))
		# After convergence, we need to remove the padding.
		for word in wordlist:
			word.letters = word.letters[1:-1]
			word.phonemes = word.phonemes[1:-1]






















