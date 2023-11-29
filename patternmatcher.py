class PatternMatcher:
	# Loads optimized dict for that lexicon if one exists, else optimizes that lexicon.
	def __init__(self, word_to_alt_domain_dict, word_to_alt_domain_filename, skip_every=-1, offset = 0):
		formatted_name = 'optimized_{}'.format(word_to_alt_domain_filename)
		# Append the skip factor if applicable.
		formatted_name = formatted_name + '_skipping-every-' + str(skip_every) if skip_every != -1 else formatted_name
		# Append offset if applicable.
		formatted_name = formatted_name + '_offset-' + str(offset) if offset != 0 else formatted_name
		import pickle
		# Check for previous optimization dict and load it if applicable.
		try:
			print('Attempting to load previous optimization for {}...'.format(word_to_alt_domain_filename))
			f = open('Data/{}'.format(formatted_name), 'rb')
			self.substring_to_alt_domain_count_dict = pickle.load(f)
			f.close()
			print('Found and loaded previously saved optimization dict.')

		except FileNotFoundError:
			print('Optimization dicts not found. Optimizing {}.'.format(word_to_alt_domain_filename))
			self.substring_to_alt_domain_count_dict = \
				PatternMatcher.generate_optimization_dict(word_to_alt_domain_dict)
			f = open('Data/{}'.format(formatted_name), 'wb')
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

	# Use input_letter_substrings_largest_first as keys of substring_to_alt_domain_count_dict[key]
	# whose values to copy into a new dict, subset_of_optimized_dict.

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
	
	# Known issue: when the input word contains multiple adjacent instances of the same match, like "inin" in "asinine",
	# there is a tendency to overmatch those matches by a TINY margin (i.e. single-digit fluctuations across a hundred thousand words).
	# given the entry word "piccinini", input "asinine" should match "picc[inin]i" and "piccin[ini]". But each "in" in "as[in][in]e" matches twice,
	# and it is utterly ambiguous WHICH parent, [inin] or [ini], should be responsible for decrementation -- bear in mind that in the
	# current implementation of optimized_dict, there is no way to determine how often "inIN..." ever overlapped with "...INi".
	# To be able to do so would require far more refactoring than what it'd be worth.
	def populate_optimized(self, input_word, verbose=False):
		import re
		# A shorter way to refer to the optimized dict
		raw_counts = self.substring_to_alt_domain_count_dict
		# Any matching key/representation pair with length l >= 3 has two subkeys/sub_representations of length length l - 1. 
		# During generate_optimization_dict, those subkeys were incremented as a result of matches with this key.
		# The presence of this key therefore indicates that SOME of the subkeys' counts need to be removed. 


		matches = []

		input_letter_substrings_largest_first = PatternMatcher.generate_substrings_largest_first(input_word)

		subset_of_optimized_dict = {} # The subset of the optimized dict (substring_to_alt_domain_count) 
									  # including substrings of input_word.
		# Each greatest common ancestor will be propagated downward to its children,
		# so that it can be decremented by every ancestor's raw count.
		child_hash_to_ancestor_set_and_counts = {}
		# A unique way to refer to a given mapping.
		def make_hash(key, representation, index=-1):
			if index == -1:
				return '{}({})'.format(key, representation)
			return '[{}] {}({})'.format(index, key, representation)
		# Get the counts of each matching substring of input_word in the lexical dataset.
		# When a matched representation exists within some other matched representation, we decrement the child's counts by the parent's: 
		# i.e. given input word "catalog", some subset of entry "cat (k@t)"'s matches belong to entry "cata (k@tx)".
		for row in input_letter_substrings_largest_first:
			# row_index here is index within input_word:
			# [ 
			#   [“sauce”] 
			#   [“sauc”, “auce”], 
			#   [“sau”, “auc”, “uce”], 
			#   [“sa”, “au”, “uc”, “ce”], 
			# ]
			for row_index, key in enumerate(row):
				# Skip substrings of input_word not present in the lexical database.
				if self.substring_to_alt_domain_count_dict.get(key, None) == None:
					continue
				
				alt_domain_substring_counts = self.substring_to_alt_domain_count_dict[key].copy()  # i.e. {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}
				# Map this input substring to an inner dict of every possible representation mapped to its count
				# By the way, we must also index by row_index because substrings can have separate counts: the two "ar"s in "tartar" will have
				# separate counts because the first one is rightfully decremented by "art", for instance.
				subset_of_optimized_dict[(key, row_index)] = alt_domain_substring_counts

				# Now this substring must decrement each of its representations by their greatest common ancestors' counts
				# and flag its direct children for decrementation as well.
				alt_domain_representations = alt_domain_substring_counts.keys()
				for representation in alt_domain_representations:
					if verbose:
						print('CURRENT ROW INDEX: {},\nROW:{}\nREPRESENTATION:{}'.format(row_index, row, representation))

					key_rep_hash = make_hash(key, representation, row_index)
					if verbose:
						print('{} has {} occurrences in the lexical database.'.format(key_rep_hash, \
						alt_domain_substring_counts[representation]))

					# Set our raw count.
					subset_of_optimized_dict[(key, row_index)][representation] = raw_counts[key][representation]
					'''
					DECREMENT OURSELVES
					'''
					if key_rep_hash in child_hash_to_ancestor_set_and_counts:
						# Decrement by each greatest common ancestor.
						if verbose:
							print('  {}\'s logged successors: {}'.format(key_rep_hash, child_hash_to_ancestor_set_and_counts[key_rep_hash]))
						for ancestor_key, ancestor_representation, effective_ancestor_count, ancestor_index in child_hash_to_ancestor_set_and_counts[key_rep_hash]:
							ancestor_hash = make_hash(ancestor_key, ancestor_representation, ancestor_index)
							subset_of_optimized_dict[(key, row_index)][representation] -= effective_ancestor_count
							if verbose:
								print('  Removed {} occurrences common to ancestor {}.'.format(effective_ancestor_count, ancestor_hash))
								print('  {} now has {} occurrences.'.format(key_rep_hash, subset_of_optimized_dict[(key, row_index)][representation]))
					'''
					PASS ANCESTOR DATA TO CHILDREN
					'''
					# Short ones have no children.
					if len(key) < 3:
						continue
					# Propagate greatest ancestors downward if present, to be decremented in future iterations (see "#Decrement if applicable." above).
					# Also pass in the DECREMENTED direct parent, since those represent the manners in which that parent
					# serves as a unique greatest common ancestor itself.
					# (This explains why we go in order of largest substrings first)
					parent_decremented_counts = subset_of_optimized_dict[(key, row_index)][representation]
					parent_hash = key_rep_hash # We'll call this match parent for clarity.
					left_child_hash = make_hash(key[:-1], representation[:-1], row_index)
					right_child_hash = make_hash(key[1:], representation[1:], row_index + 1)
					if verbose:
						print('Informing {}\'s children {} and {} of its ancestors.'.format(parent_hash, left_child_hash, right_child_hash))

					left_child_set = child_hash_to_ancestor_set_and_counts.get(left_child_hash, set())
					right_child_set = child_hash_to_ancestor_set_and_counts.get(right_child_hash, set())
					if verbose:
						print('    left child set: {}\n    right child set: {}'.format(left_child_set, right_child_set))
					if parent_hash not in child_hash_to_ancestor_set_and_counts:
						if verbose:
							print('  {} itself is a greatest common ancestor'.format(parent_hash))
						# No previous parent pointed me to their counts.
						# I therefore must propagate myself downward as the greatest common ancestor to my children.

						left_child_set.add((key, representation, raw_counts[key][representation], row_index))
						right_child_set.add((key, representation, raw_counts[key][representation], row_index))
					else:
						if verbose:
							print('  {} itself had ancestors: {}'.format(parent_hash, child_hash_to_ancestor_set_and_counts[parent_hash]))
							print('  {} also adding its own counts not accounted for by those ancestors: {}'.format(parent_hash, parent_decremented_counts))
						# This parent had least one greater ancestor to pass down. Pass it down.
						left_child_set = left_child_set.union(child_hash_to_ancestor_set_and_counts[parent_hash])
						right_child_set = right_child_set.union(child_hash_to_ancestor_set_and_counts[parent_hash])
						# We arrive at the reason why we pass ancestor_count into the tuple instead of getting it from raw counts:
						# This match's direct child substrings might have counts due to this match and NOT any of its ancestors:
						# for instance, given the input word "table", current parent "ble", right child "le", greatest common ancestor "able",
						# "le" needs to be decremented by BOTH 1) counts of its grandparent "able" AND 2) the instances of "ble" without parents (in this case "coble.")
						# We did (1) above. Now we do (2).
						# (Concrete example: matching "table" in the dataset of 3 words "bund[le]", "co[ble]" and "knowledge[able]", 
						#  the raw counts of matches are le: 3, ble: 2, able: 1.
						#  The corrected counts should be le: 1 (from bundle), ble: 1 (from coble), and able: 1 (from knowledgeable).)
						left_child_set.add((key, representation, parent_decremented_counts, row_index))
						right_child_set.add((key, representation, parent_decremented_counts, row_index))

					# Update child entries.
					child_hash_to_ancestor_set_and_counts[left_child_hash] = left_child_set
					child_hash_to_ancestor_set_and_counts[right_child_hash] = right_child_set
					if verbose:
						print('    updated left child set: {}\n    updated right child set: {}'.format( \
							child_hash_to_ancestor_set_and_counts[left_child_hash], child_hash_to_ancestor_set_and_counts[right_child_hash]))
		# Populate matches with the final counts.
		for row in input_letter_substrings_largest_first:
			# again, row_index here is index within the word:
			# [ 
			#   [“sauce”] 
			#   [“sauc”, “auce”], 
			#   [“sau”, “auc”, “uce”], 
			#   [“sa”, “au”, “uc”, “ce”], 
			# ]
			for row_index, key in enumerate(row):
				# Skip instances not present.
				if subset_of_optimized_dict.get((key, row_index), None) == None:
					continue

				# Every match for this key.
				alt_domain_substring_counts = subset_of_optimized_dict[(key, row_index)].copy()  # i.e. {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}
				for alt_domain_representation in alt_domain_substring_counts:
					# A tuple of the form (substr, alternate_domain_representation, index, count)
					match = (key, alt_domain_representation, row_index, alt_domain_substring_counts[alt_domain_representation])
					if verbose:
						print(match)
					# By this point, substrings of substrings have been decremented to zero.
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
















