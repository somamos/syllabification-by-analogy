# A Python implementation of Damper & Marchand's "Aligning Text and Phonemes 
#      for Speech Technology Applications Using an EM-Like Algorithm"
# which can be read here: https://eprints.soton.ac.uk/260616/1/06-DAMPER.pdf
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

		def get(self, l, p): # Ignore dashes.
			return self.A[ self.L.index(l) ][ self.P.index(p) ].val if l != '-' and p != '-' else 0
		def set(self, l, p, val):
			if l == '-' or p == '-':
				return
			self.A[ self.L.index(l) ][ self.P.index(p) ] = val
		def iterate(self, l, p, val = 1):
			if l == '-' or p == '-':
				return
			self.A[ self.L.index(l) ][ self.P.index(p) ].val += val

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
			s += ''.join(['{:>12}'.format(p) for p in self.P]) # Print col labels.
			s += '\n'
			for i, row in enumerate(self.A):
				s += '{}'.format(self.L[i]) # Print row labels.
				for j, cell in enumerate(row):
					# Special print needed for None
					if cell.val is None:
						s += '{:>12}'.format('X') # Print starting cell.
						continue
					# Regular case
					elif type(cell.val) is not tuple:
						s += '{:>12.2e}'.format(cell.val) # Print individual cells.
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
						# Will never be used. We adhere to the REPRESENTATION CONSTRAINT described
						# in "Letter-Phoneme Alignment: An Exploration" by Jiampojamarn and Kondrak
						arrow = '->' # Arrow pointing right
					elif diff_i == -1 and diff_j == -1:
						arrow = '\\' # Arrow pointing bottom right
					elif diff_i == 0 and diff_j == 0:
						arrow = 'X' # Top left most.
					else:
						# Sanity check. This should never happen.
						print('Starting at ({}, {}) and going to ({}, {}). Diff: {}, {}' \
							.format(i, j, to_i, to_j, diff_i, diff_j))
						print('Something is very wrong.')
						exit()
					s += '{:>12}'.format(arrow)

				s += '\n'
			return s


	# Letters will map to row indices -- Phonemes, column indices -- of a
	# so-called association matrix. Each cell stores the likelihood of a given letter-to-phoneme pairing.
	def __init__(self, alphabet, phonemes, wordlist, vowel_letters = 'aeiouy', vowel_sounds = 'aAc@^WiIoOEReUuY', scale = 40, *args):
		# We stop iterating when curr_score stops changing.
		curr_score = 0
		# Add characters to represent the borders of words.
		self.LETTER_PAD = '#'
		self.PHONEME_PAD = '$'
		alphabet.append(self.LETTER_PAD)
		phonemes.append(self.PHONEME_PAD)

		# Naive pass, A^0. We're counting every instance a letter and phoneme
		# exist in the same word, the nearer the better (by index).
		A_curr = self.Matrix(alphabet, phonemes)
		for word in wordlist:
			for i, letter in enumerate(word.letters):
				for j, phoneme in enumerate(word.phonemes):
					if 'NAIVE' in args:
						A_curr.iterate(letter, phoneme)
						curr_score += 1
						continue
					# Weighted method.
					weight = scale / (1 + abs(i - j))
					# Let's also make sure they belong to the same "group."
					# It's not in the paper, but it seems intuitive enough and helps for most cases.
					matching = ((letter in vowel_letters) == (phoneme in vowel_sounds))
					prev_weight = weight
					weight *= 0.75 if not matching else 1
					# Also, I feel like the phoneme equaling the letter is a trivial positive indicator.
					weight *= 1.1 if letter == phoneme else 1
					
					A_curr.iterate(letter, phoneme, weight)
					curr_score += weight
			# Pad every word.
			word.letters = self.LETTER_PAD + word.letters + self.LETTER_PAD
			word.phonemes = self.PHONEME_PAD + word.phonemes + self.PHONEME_PAD					
		# Print A^0.
		print(A_curr)

		# Begin alignment.
		# Populates new and improved association matrix A_n.
		# given B, a matrix of pairings' likelihoods (determined by previous iteration's association matrix).
		# A_n is weighted by D's diagonal entries which describe the optimal path from the bottom right
		# to the top left of the matrix.
		def score(A_c, A_n, word):
			# Constructs the phoneme string naively each iteration.
			new_phonemes = ''
			score = 0

			# As per the paper, B's cells are determined by the current association matrix's scores.
			B = self.Matrix(word.letters, word.phonemes, A_c)
			# The maximums will be propagated downward and rightward through C in pursuit of an optimal path.
			C = self.Matrix(word.letters, word.phonemes)
			# D's values describe this "Expectation Maximization-like" path.
			D = self.Matrix(word.letters, word.phonemes)
			# Iterate through C, extending maximums downward and rightward and pointing D to the optimal neighbor.
			for i, ch in enumerate(word.letters):
				for j, ph in enumerate(word.phonemes):
					# Beginning cases.
					if i == 0 and j == 0:
						# Marks the path's end (while cell != None below).
						D.set_by_index(0, 0, None)
						continue
					# Topmost rows and leftmost columns are zeroes all the way through.
					elif i == 0 or j == 0: 
						# D points either leftward or upward, whichever doesn't overflow.
						# (See figure 1(b) of the paper.)
						upstream = (max(i - 1, 0), max(j - 1, 0))
						D.set_by_index(i, j, upstream)
						continue

					# Three options for predecessors:
					# 1) the cell above,
					o1 = C.get_by_index(i - 1, j)
					# 2) the cell to the left, or
					o2 = 0 			# (Disallow null letters. See "REPRESENTATION CONSTRAINT" above.)
					# 3) the cell to the top left plus current.
					o3 = C.get_by_index(i - 1, j - 1) + B.get_by_index(i, j)
					
					best = max((o1, o2, o3))

					C.set_by_index(i, j, best)
					if best == o3:
						D.set_by_index(i, j, (i - 1, j - 1))
					elif best == o2:
						D.set_by_index(i, j, (i, j - 1)) # Again, this will never happen.
					elif best == o1: 
						D.set_by_index(i, j, (i - 1, j))

					# The above order erroneously prioritizes top left over vertical in case of ties.
					# Ties should favor vertical in every case EXCEPT the bottom right:
					# For instance, double letters should be left-aligned: 'aardvark' should yield 'a-' and not '-a'
					# Whereas in the bottom right, vertical movement would cause a character to map to the padding phoneme $.
					if (o1 == o3) and (j != len(word.phonemes) - 1):
						# Rectify the tie.
						D.set_by_index(i, j, (i - 1, j))						
			#if '#aardvark#' == word.letters:
			#	print(B)
			#	print('\n\n')
			#	print(C)
			#	print('\n\n')
			#	print(D)
			#	print('\n\n\n\n\n')

			# Expectations set.
			i = len(word.letters) - 1
			j = len(word.phonemes) - 1
			# Save max (bottom right) score.
			score = C.get_by_index(i, j)
			# Now trace backwards along path described by D, build new phonemes with nulls, and populate A_next.
			cell = D.get_by_index(i, j)
			while cell != None:
				to_i, to_j = D.get_by_index(i, j)

				diff_i = to_i - i
				diff_j = to_j - j
				if diff_i == -1 and diff_j == 0:
					# Matrix D has an "arrow pointing down" at this cell.
					# Therefore, the maximum "belongs" to the row at the letter before it. Inject a null phoneme.
					new_phonemes = '-' + new_phonemes
				elif diff_i == -1 and diff_j == -1:
					# The maximum "belongs" to this letter-phoneme pair.
					new_phonemes =  D.phoneme_at(i, j) + new_phonemes
					A_n.iterate(D.letter_at(i, j), D.phoneme_at(i, j))
				elif diff_i == 0 and diff_j == -1 and i == 0:
					# Due to the REPRESENTATION CONSTRAINT, 
					# this should never happen beyond the topmost row of padding.
					# Let's not count these moments.
					break
				else:
					print('Starting at ({}, {}) and going to ({}, {}). Diff: {}, {}' \
						.format(i, j, to_i, to_j, diff_i, diff_j))
					print('The valid options have been exhausted, but none applied.')
					exit()
				# Prepare to iterate.
				cell = D.get_by_index(to_i, to_j)
				i = to_i
				j = to_j
			# Assign the new phonemes generated. The 0th character of padding has to be re-added, because
			# the top left corner only occurs at the escape case of the while loop above.
			word.phonemes = self.PHONEME_PAD + new_phonemes
			return A_n, score

		def track_progress():
			count = 0
			total = 0
			# EVALUATE PROGRESS:
			for word in wordlist:
				# (We need to add 2 because of paddings in this intermediate stage)
				if(len(word.syllable_boundary_encodings) + 2 == len(word.letters) == len(word.phonemes) ): 
					# Words with valid 1:1 mappings.
					count += 1
				total += 1
			print('{} words have valid mappings, {} don\'t'.format(count, total - count))

		prev_score = 0
		iteration = 1
		while prev_score != curr_score:
			A_next = self.Matrix(alphabet, phonemes)
			#track_progress()
			total = len(wordlist)
			prev_score = curr_score
			# Reset the score.
			curr_score = 0
			curr = 0
			for word in wordlist:
				# Score each word, adding total and returning new A.
				A_next, score_ = score(A_curr, A_next, word)
				curr_score += score_
				curr += 1
				if curr % 5000 == 0:
					# Print candidate word:
					print('Word {} has phonemes {}'.format(word.letters, word.phonemes))
					print('ITERATION {}: Scored {}/{} words.'.format(iteration, curr, total))
			print('Previous score: {}. Current score: {}'.format(prev_score, curr_score))
			iteration += 1
			# Prepare to iterate.
			A_curr = A_next
		# After convergence, we need to remove the padding.
		for word in wordlist:
			word.letters = word.letters[1:-1]
			word.phonemes = word.phonemes[1:-1]






















