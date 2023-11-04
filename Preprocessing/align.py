# A Python implementation of Damper & Marchand's "Aligning Text and Phonemes 
#      for Speech Technology Applications Using an EM-Like Algorithm"
# which can be read here: https://eprints.soton.ac.uk/260616/1/06-DAMPER.pdf

# Improvements over the original paper:
# - Discourages right-alignment without destroying valid silent letters.
#   (ctrl+f: "Suppress above the diagonal")
# - Uses "association dict" instead of "association matrix."
#   About 60% performance boost (from ~5 seconds down to ~3 seconds per 10,000 words scored).
# - Suppresses phoneme and vowel types that do not match.
#   ctrl+f: "Tune the weights"

class Aligner:
	# An matrix, A, of dimension L by P
	# A list, L, of row labels
	# A list, P, of column labels
	# Methods to access cells by index and via label.
	class Matrix:
		# Constructs L from rows, P from cols, and initial values
		# for those cells via dict by init_dict.
		def __init__(self, rows, cols, init_dict = None):
			# Map all phonemes and letters to indices.
			self.L = rows
			self.P = cols
			self.A = []
			for i in self.L:
				row = []
				for j in self.P:
					val = 0 if init_dict is None else init_dict.get(i + j, 0)
					row.append( val )
				self.A.append(row)
		# Retrieve a tuple of labels for a given index.
		def labels_at_index(self, i, j):
			return (self.L[ i ], self.P[ j ])

		# The next three methods index directly into A, bypassing row/col labels.
		def value_at_index(self, i, j):
			return self.A[ i ][ j ]

		def set_by_index(self, i, j, val):
			self.A[ i ][ j ] = val

		def iterate_by_index(self, i, j):
			self.A[ i ][ j ] += 1

		def contains(self, l, p):
			return (l in self.L) and (p in self.P)

		# Get the value associated with the cell of row label l and column label p.
		def get(self, l, p):
			# Mapping validity.
			if not self.contains(l, p):
				return 0
			return self.value_at_index( self.L.index(l), self.P.index(p) )

		# Set the value associated with the cell of row label l and column label p.
		def set(self, l, p, val):
			self.set_by_index( self.L.index(l), self.P.index(p), val )

		# Iterate, if applicable, the value associated with the cell of row label l and column label p.
		def iterate(self, l, p, val = 1):
			# Mapping validity.
			if not self.contains(l, p):
				return
			# Type validity.
			if not self.is_number( self.A[ self.L.index(l) ][ self.P.index(p) ] ):
				print('Warning. The type of the value at indices labeled ({}, {}) cannot be iterated.'.format(l, p))
				return
			# Iterate.
			self.A[ self.L.index(l) ][ self.P.index(p) ] += val

		def is_number(self, x):
			import numbers
			return isinstance(x, numbers.Number)

		def __str__(self):
			# Formatting stuff.
			SPACING = '{:>12}'
			NOTATION = '{:.2e}'

			s = ' '
			s += ''.join(['{:>12}'.format(p) for p in self.P]) # Print col labels.
			s += '\n'
			for i, row in enumerate(self.A):
				s += '{}'.format(self.L[i]) # Print row labels.
				for val in row:
					# Print cells.
					cell_str = ''
					# Format as number.					
					if self.is_number(val):
						cell_str = SPACING.format( NOTATION.format( val ) )
					# Format as tuple.
					elif type( val ) is tuple:
						# Retrieve labels pointed to by this cell.
						labels = self.labels_at_index( val[0], val[1] )
						coords_str = str(''.join(list(labels)))
						cell_str = SPACING.format( coords_str ) 
					# Convert to string.
					else:
						cell_str = SPACING.format( str( val ) )
					s += cell_str
				s += '\n'
			return s


	# Letters will map to row indices -- Phonemes, column indices -- of a
	# so-called association matrix. Each cell stores the likelihood of a given letter-to-phoneme pairing.
	def __init__(self, alphabet, phonemes, wordlist, vowel_letters = 'aeiouy', vowel_sounds = 'aAc@^WiIoOEReUuYx', scale = 40, test_words = ['auction', 'articulated', 'thanked', 'watched'], *args):
		import math
		# We stop iterating when curr_score stops changing.
		curr_score = 0
		# Add characters to represent the borders of words.
		self.LETTER_PAD = '#'
		self.PHONEME_PAD = '$'
		alphabet.append(self.LETTER_PAD)
		phonemes.append(self.PHONEME_PAD)
		# Using a dict for the "association matrix" might be more efficient.
		A_curr = {}

		# Weighted pass, A^0. We're counting every instance a letter and phoneme
		# exist in the same word, the nearer the better (by index).
		for word in wordlist:
			for i, letter in enumerate(word.letters):
				for j, phoneme in enumerate(word.phonemes):
					if 'NAIVE' in args:
						A_curr.iterate(letter, phoneme)
						curr_score += 1
						continue
					# Weighted method.
					weight = scale / (1 + abs(i - j))
					# Tune the weights:
					# 1) Make sure they belong to the same "group."
					matching = ((letter in vowel_letters) == (phoneme in vowel_sounds))
					prev_weight = weight
					weight *= 0.5 if not matching else 1
					# 2) Boost when phoneme equals letter.
					weight *= 1.1 if letter == phoneme else 1
					# 3) Manual tweaks. 
					# - letter r is mapping to vowel phoneme R in "ur" words, which makes no sense.
					# Similarly, schwa is mapping to 'n' in rare cases.
					weight *= 0.5 if letter == 'r' and phoneme == 'R' else 1
					weight *= 0.5 if letter == 'n' and phoneme == 'x' else 1
					# Populate dict.
					A_curr[letter + phoneme] = A_curr.get(letter + phoneme, 0) + weight
					curr_score += weight
			# Pad every word.
			word.letters = self.LETTER_PAD + word.letters + self.LETTER_PAD
			word.phonemes = self.PHONEME_PAD + word.phonemes + self.PHONEME_PAD					
		# Print A^0.
		#print(A_curr)

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

			# Suppress above the diagonal.
			# Severely discourage beginning with null phonemes.
			for i, i_v in enumerate(word.letters):
				for j, j_v in enumerate(word.phonemes):
					# Words like 'knowledge', 'psychology', 'gnome', and 'pterodactyl' are very rare,
					# and in e.g. the lattermost case, "t" should easily overcome the dampening to surpass "p".
					suppression_factor = math.pow(abs( 1 / (max (0, j - i ) + 1 ) ), 3)
					# dampening amounts to, for e.g. dimension 6 x 6 (Not to scale)
					#     l    E    t    -    R    -
					# L  1.0, 0.5, 0.3, 0.3, 0.2, 0.1
					# E  1.0, 1.0, 0.5, 0.3, 0.2, 0.2
					# T  1.0, 1.0, 1.0, 0.5, 0.3, 0.2
					# T  1.0, 1.0, 1.0, 1.0, 0.5, 0.3
					# E  1.0, 1.0, 1.0, 1.0, 1.0, 0.5
					# R  1.0, 1.0, 1.0, 1.0, 1.0, 1.0

					curr = B.value_at_index(i, j)
					B.set_by_index(i, j, curr * suppression_factor)

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
					o1 = C.value_at_index(i - 1, j)
					# 2) the cell to the left, or
					o2 = 0 			# (Disallow null letters due to representation constraint.
					# 3) the cell to the top left plus current.
					o3 = C.value_at_index(i - 1, j - 1) + B.value_at_index(i, j)
					
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

			if word.letters in ['#{}#'.format(x) for x in test_words]:
				print('Matrix B for {}'.format(word.letters))
				print(B)
				print('\n\n')
				print('Matrix C for {}'.format(word.letters))
				print(C)
				print('\n\n')
				print('Matrix D for {}'.format(word.letters))
				print(D)
				print('\n\n\n\n\n')

			# Expectations set.
			i = len(word.letters) - 1
			j = len(word.phonemes) - 1
			# Save max (bottom right) score.
			score = C.value_at_index(i, j)
			# Now trace backwards along path described by D, build new phonemes with nulls, and populate A_next.
			cell = D.value_at_index(i, j)
			while cell != None:
				to_i, to_j = D.value_at_index(i, j)

				diff_i = to_i - i
				diff_j = to_j - j
				if diff_i == -1 and diff_j == 0:
					# Matrix D has an "arrow pointing down" at this cell.
					# Therefore, the maximum "belongs" to the row at the letter before it. Inject a null phoneme.
					new_phonemes = '-' + new_phonemes
				elif diff_i == -1 and diff_j == -1:
					# The maximum "belongs" to this cell's letter-phoneme pair.
					letter, phoneme = D.labels_at_index(i, j)
					new_phonemes =  phoneme + new_phonemes
					A_n[letter + phoneme] = A_n.get(letter + phoneme, 0) + 1
				elif diff_i == 0 and diff_j == -1 and i == 0:
					# this should never happen beyond the topmost row of padding.
					# Let's not count these moments.
					break
				else:
					print('Starting at ({}, {}) and going to ({}, {}). Diff: {}, {}' \
						.format(i, j, to_i, to_j, diff_i, diff_j))
					print('The valid options have been exhausted, but none applied.')
					exit()
				# Prepare to iterate.
				cell = D.value_at_index(to_i, to_j)
				i = to_i
				j = to_j
			# Assign the new phonemes generated. The 0th character of padding has to be re-added, because
			# the top left corner only occurs at the escape case of the while loop above.
			word.phonemes = self.PHONEME_PAD + new_phonemes
			return A_n, score

		prev_score = 0
		iteration = 1
		while prev_score != curr_score:
			A_next = {}
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
				if curr % 10000 == 0 or word.letters in ['#{}#'.format(x) for x in test_words]:
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






















