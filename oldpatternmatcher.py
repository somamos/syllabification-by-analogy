# populate_precalculated_legacy was the previous best method, offering "complete pattern matching".
# populate_legacy offers "partial pattern matching" ("complete" and "partial" refer to M&D's usage of
# the terms in "Can syllabification improve pronunciation by analogy of English?")

# Only populate_legacy benefits from multiprocessing, presumably because populate_precalculated_legacy
# uses the re module already written in C.

# Keeping this here because even though their results are near-identical; the new, optimized PatternMatcher 
# still differs from populate_precalculated in a few edge cases. I hope to examine these differences
# in closer detail.
class OldPatternMatcher:
	def __init__(self):
		pass

	@staticmethod
	def populate(input_word, entry_word, phonemes, entry_substrings=None):
		if entry_substrings==None:
			# Partial matching.
			return OldPatternMatcher.populate_legacy(input_word, entry_word, phonemes)
		# Complete matching, should be identical to optimized method in patternmatcher.py
		return OldPatternMatcher.populate_precalculated_legacy(input_word, entry_word, phonemes, entry_substrings)


	@staticmethod
	def manage_batch_populate(pl, input_word, lexical_database, substring_database, verbose=False):
		import multiprocessing as mp
		import math
		# Chunking dicts courtesy https://stackoverflow.com/a/66555740/12572922
		def chunks(data, data2=None, SIZE=10000):
			from itertools import islice
			it1 = iter(data)
			if data2==None:
				for i in range(0, len(data), SIZE):
					yield {k:data[k] for k in islice(it1, SIZE)}
				return

			it2 = iter(data2)
			for i in range(0, len(data), SIZE):
				yield {k:data[k] for k in islice(it1, SIZE)}, {k:data2[k] for k in islice(it2, SIZE)}
		# Spawns multiple processes for matching patterns within the lexical database.
		num_processes = mp.cpu_count()
		pool = mp.Pool(processes=num_processes)
		if substring_database is None:
			processes = [pool.apply_async(OldPatternMatcher.populate_batch, args=( \
				input_word, lexical_subset)) \
				for lexical_subset in chunks(lexical_database, SIZE=math.ceil(len(lexical_database)/num_processes)) ]
		# Better method (unfortunately does not benefit from multiprocessing.)
		else:
			processes = [pool.apply_async(OldPatternMatcher.populate_batch, args=( \
				input_word, lexical_subset, substring_subset)) \
				for lexical_subset, substring_subset in chunks(lexical_database, substring_database, SIZE=math.ceil(len(lexical_database)/num_processes)) ]

		list_of_lists_of_matches = [p.get() for p in processes]
		matches = [item for sublist in list_of_lists_of_matches for item in sublist]
		for match in matches:
			if match == []:
				continue
			pl.add(*match)
		return pl, len(matches)

	# Search for matches of the smaller word within the larger word. "precaculated" refers to
	# all of entry word's substrings, passed in as entry_substrings.
	# This is the equivalent to Marchand & Damper's improvement:
	#   beginning with the end of the shorter word aligned with the start of the longer word, and 
	#   ending with the start of the shorter word aligned with the end of the longer word.
	# 
	#        FROM       ->           TO
	# alignment|||||||  ->  |||||||alignment
	# |||||||malignant  ->  malignant|||||||
	# 
	# Returns matches, a list of tuples representing matching substrings to add to the lattice.
	@staticmethod
	def populate_precalculated_legacy(input_word, entry_word, phonemes, entry_substrings, verbose=False):
		matches = []
		def add_entry(substr_index_tuple, bigger_w, length_diff):
			import re
			substr, i = substr_index_tuple
			indices_in_bigger = [m.start() for m in re.finditer('(?={})'.format(substr), bigger_w)]
			# Add to the lattice.
			for bigger_index in indices_in_bigger:
				# Entry word is the bigger word.
				if length_diff <= 0:
					# The smaller word's starting index, then, is i, because of how input_precalculated_substrings are organized.
					# Locate the indices in the entry word out of which to slice the phonemes.
					matches.append((substr, phonemes[bigger_index : bigger_index + len(substr)], i, entry_word))
					if verbose:
						print('      Adding match {}'.format(matches[-1]))
				# Input word is the bigger word.
				else:
					matches.append((substr, phonemes[i : i + len(substr)], bigger_index, entry_word))
					if verbose:
						print('      Adding match {}'.format(matches[-1]))

		length_difference = len(input_word) - len(entry_word)
		# Input word is shorter.
		if length_difference <= 0:
			# Maps every possible substring greater than length 2 to their first index of occurrence
			# in order, conveniently, from smallest to largest (per starting index), i.e.:
			# in, ind, inde, index
			# nd, nde, ndex,
			# de, dex
			# ex
			# Much of the logic that follows hinges upon this ordering.
			smaller_words_substrings = [[input_word[i:j] for j in range(i, len(input_word) + 1) \
				if j - i > 1] for i in range(0, len(input_word) - 1)]
			bigger_word = entry_word
		else:
			# entry_substrings were precalculated and are ordered as smaller_words_substrings above.
			smaller_words_substrings = entry_substrings
			bigger_word = input_word
		preserved_prev_substring_match = ''
		if verbose:
			print('Smaller words\' substrings: {}'.format(smaller_words_substrings))
		NO_MATCH = ('', -1)
		# PART 1: Prevent LEFT-ALIGNED substrings of matches, themselves, from matching.
			# A tuple saving the previous match and its index.
			# Due to the sorted order of (both input's and entries') precalculated substrings,
			# A first NON-match often implies the previous substring DID match.
			# To avoid double counting smaller sections of the same substring e.g.:
			# to,
			# tor,
			# tori,
			# we must only add items after the first nonmatch.
		prev_matching_substring = NO_MATCH
		# PART 2: Prevent RIGHT-ALIGNED substrings of matches, themselves, from matching.
			# The above fix does not prevent
			# tori,
			#  ori,
			#   ri
			# from matching.
			# ['cl', 'cla', 'clam', 'clamp', 'clamps']
			# ['la', 'lam', {lamp}, 'lamps']
			# [<am>, <amp>, 'amps']
			# [<mp>, 'mps']
			# ['ps']
			# If the curly braced entry above matches, (but the one after it doesn't)
			# we must log the index of the match, k, say, and disregard the next n rows' first k - n indices.
		prev_match_i_and_j = (0, 0)
		rows_since_last_match = 0
		has_matched = False
		for i, row in enumerate(smaller_words_substrings):
			rows_since_last_match += 1 if has_matched else 0
			for j, substring in enumerate(row):
				if substring not in bigger_word:
					# Ignore when NEVER had a match.
					if prev_matching_substring == NO_MATCH:
						break
					# See PART 1 above for reasoning.
					has_added_largest_match = True
					add_entry(prev_matching_substring, bigger_word, length_difference)
					# Flush the buffer so we know, upon loop end, whether the last remaining prev_match
					# has been accounted for. (Imagine a scenario where the very last checked substring
					# happens to perfectly match. In such cases, the "substring not in bigger_word" branch
					# would never run. Therefore, we must check for prev_match after the loop as well.)
					preserved_prev_substring_match = prev_matching_substring # Preserve this for debug.
					prev_matching_substring = NO_MATCH
					# The above case also guarantees no more matches in this row.
					break
				# Substring is in bigger word. As per PART 2 above,
				# we must ascertain this current column "does not lie in a previous mask's shadow."
				elif not has_matched:
					# Reset rows since last match.
					has_matched = True
					rows_since_last_match = 0
					# Store this in the buffer to be added upon first lack of match.
					prev_matching_substring = (substring, i)
					prev_match_i_and_j = i, j # see PART 2 above for reasoning.
					if verbose:
						print('PASS ON FIRST MATCH')
						print('  {} will be added later...'.format(prev_matching_substring))
				elif has_matched and j > (prev_match_i_and_j[1] - rows_since_last_match):
					prev_matching_substring = (substring, i)
					prev_match_i_and_j = i, j # see PART 2 above for reasoning.
					if verbose:
						print(' PASS: {} > {} - {}'.format(j, prev_match_i_and_j[1], rows_since_last_match))
						print('  {} will be added later...'.format(prev_matching_substring))
				else:
					if verbose:
						print(' FAIL: {} >= {} - {}'.format(j, prev_match_i_and_j[1], rows_since_last_match))
						print('  {}: Skipping right-aligned substring  "{}" of previous match.'.format( \
							entry_word, substring))
					pass

			if prev_matching_substring != NO_MATCH:
				# Add previous entry.
				add_entry(prev_matching_substring, bigger_word, length_difference)
				# Flush buffer.
				prev_matching_substring = NO_MATCH

		return matches
	# The original method of Dedina and Nusbaum. Words begin left-aligned and end right-aligned.
	# Given some word (input_word) we wish to pronounce alongside some entry_word and its phonemes,
	# Return matches, a list of tuples representing matching substrings to add to the lattice.
	@staticmethod
	def populate_legacy(input_word, entry_word, phonemes):
		matches = []
		length_difference = len(input_word) - len(entry_word)
		# a is always the longer word.
		a, b = (input_word, entry_word) if length_difference >= 0 else (entry_word, input_word)
		for offset in range(abs(length_difference) + 1):
			index = -1
			length = 0
			match = ''
			char_buffer = [False, False]
			for k in range(0, len(b) + 1):
				# Iterate buffer.
				char_buffer[0] = char_buffer[1] # Begin False (default).
				char_buffer[1] = (b[k] == a[offset + k]) if k != len(b) else False # End False.
				# Currently in the middle of a match.
				if all(char_buffer):
					length += 1
					match += b[k] # Append to match.
				# Match just started.
				elif char_buffer == [False, True]:
					index = k
					length = 1
					match = b[k] # Flush match.
				# Match just ended.
				elif char_buffer == [True, False]:
					# Insufficient length.
					if length == 1:
						continue
					if length_difference < 0:
						# When the entry word is bigger, phoneme indices "shift right" to remain accurate.
						matches.append((match, phonemes[index + offset : index + offset + length], index, entry_word))
					else:
						# When the entry word is smaller, matched indices "shift right" to remain accurate.
						matches.append((match, phonemes[index : index + length], index + offset, entry_word))
		return matches

	# A group of words to be run by a single process.
	# Assumes legacy method if three arguments are passed, else uses precalculated.
	@staticmethod
	def populate_batch(input_word, entry_dict_batch, substrings_dict_batch=None):
		func = OldPatternMatcher.populate_legacy
		if substrings_dict_batch != None:
			func = OldPatternMatcher.populate_precalculated_legacy
		matches = []
		for entry_word in entry_dict_batch:
			if substrings_dict_batch == None:
				matches += func(input_word, entry_word, entry_dict_batch[entry_word])
			else:
				matches += func(input_word, entry_word, entry_dict_batch[entry_word], substrings_dict_batch[entry_word])
		return matches