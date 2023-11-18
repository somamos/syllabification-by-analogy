class PatternMatcher:
	def __init__(self, word_to_alt_domain_dict):
		import pickle
		# Check for previous optimization dict and load it if applicable.
		try:
			print('Attempting to load previous save...')
			f = open('Data/optimization_dict', 'rb')
			self.substring_to_alt_domain_count_dict = pickle.load(f)
			f.close()
			print('Found and loaded previously saved optimization dict.')

		except FileNotFoundError:
			print('Optimization dicts not found. Loading from scratch.')
			self.substring_to_alt_domain_count_dict = \
				PatternMatcher.generate_optimization_dict(word_to_alt_domain_dict)
			f = open('Data/optimization_dict', 'wb')
			pickle.dump(self.substring_to_alt_domain_count_dict, f)
			f.close()

	# 'slime' -> [['slime'], ['slim', 'lime'], ['sli', 'lim', 'ime'], ['sl', 'li', 'im', 'me']]
	@staticmethod
	def generate_substrings_largest_first(a):
		return [[a[l: l + len(a) + 1 - i] for l in range(i)] for i in range(1, len(a))]

	# 'slime' -> [['sl', 'li', 'im', 'me'], ['sli', 'lim', 'ime'], ['slim', 'lime'], ['slime']]
	@staticmethod
	def generate_substrings_smallest_first(a):
		return [[a[ i: i + l ] for i in range(len(a) - l + 1 )] for l in range(2, len(a) + 1)]

	# 'slime' -> [['sl', 'sli', 'slim', 'slime'], ['li', 'lim', 'lime'], ['im', 'ime'], ['me']]
	@staticmethod
	def generate_substrings_by_index_and_increasing_length(a):
		return [[a[i:j] for j in range(i, len(a) + 1) if j - i > 1] for i in range(0, len(a) - 1)]
	# Given a one-to-one mapping of word spellings to some alternate domain
	# (phonemes or syllables), generate and return an optimized dict:
	# "substring_to_alt_domain_count_dict", a dict of dicts of the form:
		# 
		# {
		#	...
		#	ca:		{ k@: 100, c@: 95, ke: 20, ... kA:3 }
		#	cap: 	{ k@p: 30, c@p: 60, ... kAp: 1 }
		#	capt:	{ k@pt: 20 }
		#	...
		# }
		#
		# This maps a substring's spelling to a dictionary of every representation of that substring
		# in the alternate domain. Those representations themselves map to their counts ("frequency" in M&D's article.)
		#
		# Note above how substrings of substrings' counts are necessarily more frequent than their superstrings' counterparts,
		# i.e. "k@p" must occur fewer times than "k@". We can use this fact to subtract superstring counts from substrings counts,
		# "[Preventing] ... substrings of matches, themselves, from matching" as described in pba.py's populate_precalculated.
	@staticmethod
	def generate_optimization_dict(word_to_alt_domain_dict):
		substring_to_alt_domain_count_dict = {}
		for index, word in enumerate(word_to_alt_domain_dict):
			if index%10000 == 0:
				print('Indexed {} out of {} words.'.format(index, len(word_to_alt_domain_dict)))
			alt = word_to_alt_domain_dict[word] # Representation in the alternate domain.
			substring_to_alt_domain_count_dict = PatternMatcher.add(word, alt, substring_to_alt_domain_count_dict)

		print('Done.')
		return substring_to_alt_domain_count_dict

	# Use input_letter_substrings_smallest_first as keys of substring_to_alt_domain_count_dict[key]
	# whose values to copy into a new dict, input_substrings_to_alt_domain_count.

	# Then we must prevent substrings of substrings from counting twice.
	# For instance, given the set of alternate domain representations for substrings of input word "sauce": 

	# sauce: {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}
	# sauc: {'sc--': 7, 's-Ws': 2, 'sc-s': 2}
	# auce: {'c--s': 8, 's--i': 1, '-WCE': 1, 'c-sx': 3, 'c-sI': 1, 'o-sE': 1, 'c-CE': 1, '-Wse': 2}
	# sau: {'sc-': 65, '-c-': 9, 'so-': 6, '--W': 1, 's--': 1, 's-W': 13, '---': 1, '-a-': 2, '-o-': 1}
	# auc: {'c--': 9, 'c-C': 20, '-Wk': 11, 'a-k': 6, 'o-k': 4, 'c-k': 12, 'a-K': 2, 'c-K': 5, '--k': 1, 's--': 1, '---': 5, 'x-k': 4, 'ckx': 1, '-WC': 5, 'c-s': 7, 'o-s': 1, 'o--': 3, 'a-C': 1, 'lck': 1, '-Ws': 2, 'auC': 2, '-W-': 1}
	# uce: {'--s': 9, '--i': 1, 'uCi': 1, 'uCE': 6, 'u-s': 29, 'usx': 4, 'Ysi': 1, 'WCE': 1, 'xsE': 2, 'usi': 2, 'ust': 10, 'usE': 4, '^si': 1, '-sx': 3, '-sI': 2, '-sE': 1, '---': 1, 'usI': 6, 'xCI': 1, 'YsI': 1, '-CE': 1, 'xCE': 1, 'Wse': 2}
	# sa: {'s@': 667, 's-': 122, 'ze': 15, 'zx': 93, 'sx': 382, '-x': 112, 'sE': 34, 'sa': 469, 'Xx': 5, '#@': 2, '-@': 29, '-a': 64, 'se': 262, '--': 28, 'sc': 147, 'z-': 33, 'z@': 18, '-e': 21, '-c': 10, '-i': 1, 'zc': 2, 'sI': 8, 'za': 14, '-E': 6, 'so': 6, 'zI': 5, 'I-': 3, 'sR': 1, 'zi': 2, 'Az': 1, 'X@': 2, 'zL': 3, 'sA': 1, 'sL': 2, 'xf': 1, 'sW': 1, '-o': 1, 'Za': 3}
	# au: {'x-': 28, '-W': 577, 'a-': 87, 'c-': 1122, '--': 259, 'o-': 111, '@-': 21, 'cT': 1, 'od': 1, 's-': 1, '-Y': 6, '-u': 3, 'cb': 1, 'ck': 7, 'C-': 2, 'xf': 1, 'L-': 1, 'e-': 5, 'xY': 1, 'yW': 3, 'au': 7, 'ak': 1, 'kc': 4, 'fc': 1, 'lc': 3, 'l-': 1, 'xk': 2, 'xs': 1, 'Wu': 1}
	# uc: {'^k': 406, '^K': 36, 'uC': 128, '^C': 54, '--': 20, 'xk': 60, '-x': 28, '-C': 53, 'Wk': 11, '-k': 43, '-K': 7, 'uk': 94, '^!': 2, 'u-': 51, 'us': 69, '^X': 30, 'Yk': 28, 'Ys': 5, '^Q': 4, 'xC': 12, 'kx': 1, 'WC': 5, 'xs': 2, 'Y-': 5, 'YS': 1, '^s': 2, '^-': 3, 'uS': 4, '-s': 10, 'YX': 1, '-X': 1, 'ck': 1, 'l^': 1, 'Ws': 2, 'Uk': 1, 'W-': 1}
	# ce: {'sE': 399, '-s': 1136, '-E': 104, 'sI': 182, '-i': 21, 'En': 2, 'sx': 144, 'st': 105, 'si': 132, 'se': 26, 'CE': 166, '--': 51, '-t': 7, '-x': 45, 'Is': 7, '-R': 20, 'CR': 25, 'Sx': 5, 'Ci': 14, 'XE': 10, 'Ce': 7, 'sR': 4, 'C-': 1, 'CW': 2, 'CI': 4, 'kE': 4, 'kR': 1, '-S': 14, 'SI': 1, '-I': 16, '!x': 2, 'ns': 2, '-e': 1, 'ki': 5, 'Cu': 1, 'ku': 1, '@k': 32, 'xk': 8, 'Si': 2, '-X': 4}

	# The proper count for 'sc--' is not 7 but 1: the count for 'sc--' minus the count for 'sc--s'.
	# Similarly, the proper count for 'sc-' is not 65 but 56: the count for 'sc-' minus (the counts for 'sc--' plus the counts for 'sc-s').

	# In general, given each substring s of length n > 2 with a set of alternate domain representations A_s, we must
	# subtract the counts of A_s[1:] and A_s[:-1] -- that is, the representations of A_s's sub-substrings of length n-1 -- by the counts of A_s whose 
	# alternate domain representations map onto those of the sub-substring's.

	# Returns a list of tuples of the form (substr, phonemes[i : i + len(substr)], index, count(!))
	def populate_optimized(self, input_word, verbose=False):
		matches = []
		input_letter_substrings_smallest_first = PatternMatcher.generate_substrings_smallest_first(input_word)
		# Prevent over-decrementing by adding successfully decremented "encompassing representations" to a set.
		# Over-decrementing occurs when the same substring matches twice in a word as with "tartar" and "murmur""
		decremented = set()

		input_substrings_to_alt_domain_count = {}
		for row in input_letter_substrings_smallest_first:
			for row_index, key in enumerate(row):
				# Skip instances not present.
				if self.substring_to_alt_domain_count_dict.get(key, None) == None:
					continue
				alt_domain_substring_counts = self.substring_to_alt_domain_count_dict[key].copy()  # i.e. {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}
				# Map this input substring to an inner dict of every possible representation mapped to its count
				input_substrings_to_alt_domain_count[key] = alt_domain_substring_counts

				# Now we must "prevent substring of substrings from counting twice."
				# Skip substrings who have no valid substrings.
				if len(key) <= 2:
					continue
				# Decrement left subkeys' counts by c, the CURRENT key's counts. That is, c of subkey's counts
				# are "thanks to" this current key.
				alt_domain_representations = alt_domain_substring_counts.keys()
				for representation in alt_domain_representations:
					# We prevent a single representation from decrementing its subrepresentations more than once.
					if '{}_{}'.format(key, representation) in decremented:
						if verbose:
							print('NOTICE: prevented {} ({}) from decrementing left subkey {} ({}) again.'.format(key, representation, key[:-1], representation[:-1]))
							if row_index + 1 == len(row):
								print('Right subkey {} ({}) would\'ve been decremented, too'.format(key[1:], representation[1:]))
						continue
					decremented.add('{}_{}'.format(key, representation))

					# Thanks to "smallest_first" we know that the subkeys of key_ must also 
					# be in input_substrings_to_alt_domain_count.
					left_subkey = key[:-1]
					left_altrep = representation[:-1]

					if verbose:
						print('Representation {} found in substrings.'.format(key))
						print('Left subkey: {}, Left altrep: {}'.format( \
							left_subkey, left_altrep))
						print('Current count of input_substrings_to_alt_domain_count[{}][{}]: {}'.format(left_subkey, left_altrep, \
							input_substrings_to_alt_domain_count[left_subkey][left_altrep]))
						print('Decrementing by the encompassing representation input_substrings_to_alt_domain_count[{}][{}] of count: {}'.format( \
							key, representation, input_substrings_to_alt_domain_count[key][representation]))

					input_substrings_to_alt_domain_count[left_subkey][left_altrep] -= input_substrings_to_alt_domain_count[key][representation]

					if verbose:
						print('New count of input_substrings_to_alt_domain_count[{}][{}]: {}'.format(left_subkey, left_altrep, \
							input_substrings_to_alt_domain_count[left_subkey][left_altrep]))
					# Every last item per row requires a right subkey to be decremented as well.
					if row_index + 1 < len(row):
						continue
					right_subkey = key[1:]
					right_altrep = representation[1:]
					if verbose:
						print('CURRENT SUBSTRING {} ENDS WORD {}. Right subkey must be decremented.'.format(key, input_word))
						print('Current count of input_substrings_to_alt_domain_count[{}][{}]: {}'.format(right_subkey, right_altrep, \
							input_substrings_to_alt_domain_count[right_subkey][right_altrep]))
						print('Decrementing by the encompassing representation input_substrings_to_alt_domain_count[{}][{}] of count: {}'.format( \
							key, representation, input_substrings_to_alt_domain_count[key][representation]))
					
					input_substrings_to_alt_domain_count[right_subkey][right_altrep] -= input_substrings_to_alt_domain_count[key][representation]

					
					if verbose:
						print('New count of input_substrings_to_alt_domain_count[{}][{}]: {}'.format(right_subkey, right_altrep, \
							input_substrings_to_alt_domain_count[right_subkey][right_altrep]))
		# Populate matches with the final counts.
		for row in input_letter_substrings_smallest_first:
			# row_index here is index within the word:
			# [ 
			#   [“sa”, “au”, “uc”, “ce”], 
			#   [“sau”, “auc”, “uce”], 
			#   [“sauc”, “auce”], 
			#   [“sauce”] 
			# ]
			for row_index, key in enumerate(row):
				# Skip instances not present.
				if input_substrings_to_alt_domain_count.get(key, None) == None:
					continue

				# Every match for this key.
				alt_domain_substring_counts = input_substrings_to_alt_domain_count[key].copy()  # i.e. {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}
				for alt_domain_representation in alt_domain_substring_counts:
					# A tuple of the form (substr, alternate_domain_representation, index, count)
					match = (key, alt_domain_representation, row_index, alt_domain_substring_counts[alt_domain_representation])
					if verbose:
						print(match)
					# By this point, substrings of substrings have been decremented to zero.
					# We print before pruning them just to be able to verify that the logic is sound.
					if alt_domain_substring_counts[alt_domain_representation] == 0:
						continue
					if alt_domain_substring_counts[alt_domain_representation] < 0:
						# Given "substrings of substrings' counts are necessarily more frequent than their superstrings' counterparts",
						# This should never happen.
						print('WARNING. Logic was not sound with representation "{}" of count {}.'.format(alt_domain_representation, \
							alt_domain_substring_counts[alt_domain_representation]))
					matches.append(match)
		return matches

	# A nice and encapsulated way to put a word back after cross-validation.
	def replace(self, input_word, input_altrep):
		self.substring_to_alt_domain_count_dict = \
			PatternMatcher.add(input_word, input_altrep, self.substring_to_alt_domain_count_dict)


	# Populate dict d with word input_word and its alternate representation input_altrep.
	# This method is also used to put a word back after leave-one-out cross-validation.
	@staticmethod
	def add(input_word, input_altrep, d, verbose=False):
		# d is substring_to_alt_domain_count_dict, 
		substrings = PatternMatcher.generate_substrings_by_index_and_increasing_length(input_word)
		substrings_alt = PatternMatcher.generate_substrings_by_index_and_increasing_length(input_altrep)
		for i, row in enumerate(substrings):
			# Populate dict iterating by this word's mappings.
			for j, substring in enumerate(row):
				substr_alt = substrings_alt[i][j]
				# Get or instantiate this substring's counts.
				entry = d.get(substring, {})
				# Iterate count of this alternate domain representation.
				entry[substr_alt] = entry.get(substr_alt, 0) + 1
				# Update this substring's counts.
				d[substring] = entry
		return d

	# For cross-validation.
	# This is kind of like un-blending a smoothie.
	# If the entire input word exists in the dict, we must first decrement its alternate domain representation
	# from the entry (deleting the entire entry if its was the only such representation.)
	# Then do the same thing for all its substrings (decrementing or deleting substrings' alt domain representations)

	# Don't forget to add it back later!
	# Returns true if removed. Returns false if it didn't exist in the first place.
	def remove(self, input_word, input_altrep, verbose=False):
		if verbose:
			print('Attempting to remove {} ({}) from the optimized dataset'.format(input_word, input_altrep))
		# Helper function.
		def decrement_or_delete(sub_input, sub_altrep):
			nonlocal input_word
			entry = self.substring_to_alt_domain_count_dict.get(sub_input, None)
			if entry == None and input_word != sub_input:
				print('Warning. Input {} was found, but its substring ({}) was not found.'.format(input_word, sub_input))
				exit()
			elif entry == None:
				# Good, we didn't have this word in the first place.
				print('Optimization dict did not have this word.')
				return False

			# Okay, now we know we exist. remove ourselves from that entry.
			count = entry.get(sub_altrep, -1)
			if count <= -1:
				print('Warning. The input word exists in optimized dict, but NOT with the provided ground truth alternate domain representation.')
			elif count == 0:
				print('Warning. The input word\'s provided alternate domain representation was at count zero. This should never happen.')
			elif count == 1:
				if verbose:
					print('Removing input word\'s alternate domain representation {} from entry.'.format(sub_altrep))
				del entry[sub_altrep]
				if len(entry) == 0:
					if verbose:
						print('That was the only representation. Removing {} from main dict as well.'.format(sub_input))
					del self.substring_to_alt_domain_count_dict[sub_input]
			else:
				# We only decrement.
				if verbose:
					print('Successfully decremented {} from {}.'.format(sub_altrep, sub_input))
				entry[sub_altrep] -= 1
		# Main loop of the method.
		input_word_substrings = PatternMatcher.generate_substrings_largest_first(input_word)
		input_altrep_substrings = PatternMatcher.generate_substrings_largest_first(input_altrep)
		for i, row in enumerate(input_word_substrings):
			for j in range(len(row)):
				decrement_or_delete(input_word_substrings[i][j], input_altrep_substrings[i][j]) 
		return True

	@staticmethod
	def copy_dict(a):
		copy = {}
		for key in a:
			copy[key] = a[key].copy()
		return copy
	# For a given word and its representation, returns true when 
	# removal of this word "should" change inverse_dict by virtue of wiping out
	# the entire existence of at least one of its substrings' letter-to-alternate-domain representations.
	def all_substring_counts_greater_than_one(self, word, altrep):
		# Check largest first, because they're the most likely to about to be deleted.
		word_substrings = PatternMatcher.generate_substrings_largest_first(word)
		altrep_substrings = PatternMatcher.generate_substrings_largest_first(altrep)
		for i, substrings_row in enumerate(word_substrings):
			for j, substring in enumerate(substrings_row):
				subaltrep = altrep_substrings[i][j]
				# At least one substring is about to be deleted entirely.
				if self.substring_to_alt_domain_count_dict[substring][subaltrep] == 1:
					return False
		return True

	# Removing a word and adding it back should not permanently change the contents of either dict.
	# Cross validation should leave no trace! or else the dict will deteriorate over the course of the test.
	# When check_every = -1, we check every single iteration. This is very, very slow.
	# Otherwise, check_every must be 2 or more due to modulo.
	def simulate_leaveoneout(self, ground_truth_dict, check_every=-1):
		if check_every != -1 and check_every <2:
			print('NO. check_every must equal -1 OR be above 1.')
			exit()
		words_tested = 0
		is_test_round = False # Checking for dict equality is hugely expensive.
		# Let's only test every once in a while.
		has_failed = False # Also, only copy dicts again after you've failed.

		total_tests = 0
		total_failures = 0

		# Let's just refer to them this way, it's easier to type.
		d_ = self.substring_to_alt_domain_count_dict
		# Copy at the beginning.
		d_pre = PatternMatcher.copy_dict(d_)

		for word in ground_truth_dict:
			# Print updates periodically.
			# We test every representation of every word.
			representation = ground_truth_dict[word]
			
			if check_every == -1 or ((words_tested)%check_every == 0):
				print('{} / {} ({:.2f}%) words have been tested.'.format( \
					words_tested, len(ground_truth_dict), \
					100*words_tested/len(ground_truth_dict)))
				print('TEST COUNT: {} FAILURE COUNT: {}'.format(total_tests, total_failures))
				is_test_round = True # Reset this.
				# Flush copy.
				if has_failed:
					d_pre = PatternMatcher.copy_dict(d_)
				has_failed = False

			# Remove the word.
			self.remove(word, representation)
			# TEST ROUND BARRIER 1
			if is_test_round:
				# Make sure the dicts are NOT equal.
				if d_ == d_pre:
					print('WARNING. The removal of {} ({}) did not change the optimized dict.'.format(word, representation))
					total_failures += 1
					has_failed = True
			# Add the word back.
			self.replace(word, representation)

			# TEST ROUND BARRIER 2
			if is_test_round:

				# Make sure the dicts ARE equal.
				if d_ != d_pre:
					print('WARNING. Removal and replacement of {} ({}) has permanently altered the optimized dict.'.format(word, representation))
					total_failures += 1
					has_failed = True
				# "total_failures" has had the opportunity to increment two times.
				total_tests += 2
				is_test_round = False
			words_tested += 1
		print('Test complete. Out of {} opportunities to fail, {} tests actually failed.'.format(total_tests, total_failures))
















