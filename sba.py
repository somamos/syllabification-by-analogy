# Syllabification By Analogy
# Implements the method described in Marchand & Damper's 
# "Can syllabification improve pronunciation by analogy of English?

from lattice import Lattice, ERRORS

class SyllabifierByAnalogy():

	def cross_validate(self, start=0):
		from datetime import datetime
		from collections.abc import Iterable
		now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
		total = 0
		trial = start
		trial_count = len(self.lexical_database) - 1
		trial_word = ''
		ground_truth = ''
		# Map the strategy name to the titular stat.
		words_correct = {}
		words_total = {}
		junctures_correct = {}
		junctures_total = {}
		with open('Data/Syllabification_Results_{}.txt'.format(now), 'w', encoding='latin-1') as f:
			def end_trial(output):
				nonlocal trial
				f.write(output)
				trial += 1
			# Iterate the occurrences of this error. Return the line to append to the file.
			def count_error(code):
				description = ERRORS[code]
				self.simple_print(code)
				# Log instance of error code.
				words_total[description] = words_total.get(description, 0) + 1
				# Print results.
				return '{}, {}\n\n'.format(description, words_total.get(description, 0))

			while trial < trial_count:
				output = ''
				i = 0
				skipped = False
				
				keys = list(self.lexical_database.keys())

				trial_word = keys[trial]
				#trial_word = self.add_junctures(trial_word)
				output += 'TRIAL {}, {}\n'.format(trial, trial_word)
				ground_truth = self.lexical_database[trial_word]
				print('Loading trial #{}: {} ({})...'.format(trial, trial_word, ground_truth))

				results = self.cross_validate_syllabify(trial_word)
				if not isinstance(results, Iterable):
					# Print the error.
					error_code = results
					output += count_error(error_code)
					end_trial(output)
					continue

				for key in results:
					# Iterate words for which this trial had a result.
					words_total[key] = words_total.get(key, 0) + 1
					# Evaluate that result.
					if results[key].pronunciation == ground_truth:
						words_correct[key] = words_correct.get(key, 0) + 1
					# Iterate JUNCTURES for which this trial had a result.
					for index, ch in enumerate(results[key].pronunciation):
						# Skip non-junctures.
						if ch not in '|*':
							continue
						# Total always iterates.
						junctures_total[key] = junctures_total.get(key, 0) + 1
						if index < len(ground_truth) and ch == ground_truth[index]:
							# Correct only when correct.
							junctures_correct[key] = junctures_correct.get(key, 0) + 1
				for key in results:
					output += '{}, {}, {}, {}, {}\n'.format(key, words_correct.get(key, 0), words_total.get(key, 0), \
						junctures_correct.get(key, 0), junctures_total.get(key, 0))
					print('{}: {}, Correct?: {}. {}/{} words correct ({:.2f}%), {}/{} junctures correct ({:.2f}%)'.format( \
						key, results[key].pronunciation, results[key].pronunciation == ground_truth, \
						words_correct.get(key, 0), words_total.get(key, 0), 100*words_correct.get(key, 0)/words_total.get(key, 1), \
						junctures_correct.get(key, 0), junctures_total.get(key, 0), 100*junctures_correct.get(key, 0)/junctures_total.get(key, 0)))
				output += '\n'
				end_trial(output)
				# Total only increments after a nonskipped trial.
				total += 1
				print()

	# Removes input word from the dataset before pronouncing if present.
	# Returns a dict of string labels per strategy mapped to pronunciation results.
	def cross_validate_syllabify(self, input_word, verbose=False):
		input_word = self.add_junctures(input_word)

		trimmed_lexical_database = {}
		trimmed_substring_database = {}

		answer = ''
		found = False
		for word in self.lexical_database.keys():
			if word != input_word:
				trimmed_lexical_database[word] = self.lexical_database[word]
				trimmed_substring_database[word] = self.substring_database[word]
			else:
				found = True
				answer = self.lexical_database[word]
				if verbose:
					print('Removed {} ({}) from dataset.'.format(input_word, answer))
		if not found:
			print('The dataset did not have {}.'.format(input_word))
		results = self.syllabify(input_word, (trimmed_lexical_database, trimmed_substring_database), verbose=False)
		if verbose:
			self.simple_print(results, answer)

		return results

	def syllabify(self, input_word, trimmed_databases=None, verbose=False):
		# Junctures added?
		input_word = self.add_junctures(input_word)

		# Default to the database loaded in the constructor.
		lexical_database = self.lexical_database
		substring_database = self.substring_database

		# Refer to pruned versions when called by cross_validate_syllabify.
		if trimmed_databases != None:
			lexical_database = trimmed_databases[0]
			substring_database = trimmed_databases[1]
		if verbose:
			print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		self.pl = Lattice(input_word)

		# Bigrams unrepresented in the dataset will cause gaps in lattice paths.
		self.pl.flag_unrepresented_bigrams(input_word, lexical_database)

		# Second fastest.
		# The original method of Dedina and Nusbaum. Words begin left-aligned and end right-aligned.
		def populate_legacy():
			nonlocal input_word
			nonlocal entry_word
			nonlocal syllable_domain
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
							self.pl.add(match, syllable_domain[index + offset : index + offset + length], index)
						else:
							# When the entry word is smaller, matched indices "shift right" to remain accurate.
							self.pl.add(match, syllable_domain[index : index + length], index + offset)
		# Maps every possible substring greater than length 2 to their first index of occurrence
		# in order, conveniently, from smallest to largest (per starting index).
		input_precalculated_substrings = [[input_word[i:j] for j in range(i, len(input_word) + 1) if j - i > 1] for i in range(0, len(input_word) + 1)]
		# Every word has their substrings precalculated. Search for the smaller word
		# in the larger word. This is the equivalent to Marchand & Damper's improvement
		# of beginning with the end of the shorter word aligned with the start of the longer word,
		# ending with the start of the shorter word aligned with the end of the longer word, E.G.:
		#        FROM       ->           TO
		# alignment         ->         alignment
		#        malignant  ->  malignant
		def populate_precalculated():
			def add_entry(substr_index_tuple, bigger_w, length_diff):
				import re
				substr, i = substr_index_tuple
				indices_in_bigger = [m.start() for m in re.finditer('(?={})'.format(substr), bigger_w)]
				# Add to the lattice.
				for bigger_index in indices_in_bigger:
					# Entry word is the bigger word.
					if length_diff <= 0:
						# The smaller word's starting index, then, is i, because of how input_precalculated_substrings are organized.
						# Locate the indices in the entry word out of which to slice the syllable_domain.
						self.pl.add(substr, syllable_domain[bigger_index : bigger_index + len(substr)], i)
					# Input word is the bigger word.
					else:
						self.pl.add(substr, syllable_domain[i : i + len(substr)], bigger_index)
			# TODO: Only match upon a break. That way,
			# to,
			# tor,
			# tori,
			# these substrings won't get double counted.
			nonlocal input_precalculated_substrings
			nonlocal input_word
			nonlocal entry_word
			nonlocal syllable_domain
			length_difference = len(input_word) - len(entry_word)
			# Input word is shorter.
			if length_difference <= 0:
				smaller_words_substrings = input_precalculated_substrings
				bigger_word = entry_word
			else:
				smaller_words_substrings = substring_database[entry_word]
				bigger_word = input_word

			NO_MATCH = ('', -1)
			# A tuple saving the previous match and its index.
			# Due to the sorted order of (both input's and entries') precalculated substrings,
			# A first NON-match often implies the previous substring DID match.
			# To avoid double counting smaller sections of the same substring e.g.:
			# to,
			# tor,
			# tori,
			# we must only add items after the first nonmatch.
			prev_matching_substring = NO_MATCH
			for i, row in enumerate(smaller_words_substrings):
				for j, substring in enumerate(row):
					if substring not in bigger_word:
						# Ignore when NEVER had a match.
						if prev_matching_substring == NO_MATCH:
							break
						# See "to, tor, tori" above for reasoning.
						#print('{} is being added!'.format(prev_matching_substring))
						add_entry(prev_matching_substring, bigger_word, length_difference)
						# Flush the buffer so we know, upon loop end, whether the last remaining prev_match
						# has been accounted for. (Imagine a scenario where the very last checked substring
						# happens to perfectly match. In such cases, the "substring not in bigger_word" branch
						# would never run. Therefore, we must check for prev_match after the loop as well.)
						prev_matching_substring = NO_MATCH
						# The above case also guarantees no more matches in this row.
						break
					else:
						# Store this in the buffer to be added upon first lack of match.
						prev_matching_substring = (substring, i)
						#print('{} will be added later...'.format(prev_matching_substring))
				if prev_matching_substring != NO_MATCH:
					add_entry(prev_matching_substring, bigger_word, length_difference)
		for entry_word in lexical_database:
			syllable_domain = lexical_database[entry_word]
			#populate_precalculated()
			populate_legacy()
		candidates = self.pl.find_all_paths()
		results = self.pl.decide(candidates)
		# Print with no regard for ground truth.
		if verbose:
			self.simple_print(results)
		return results

	# It's safe to call this repeatedly.
	def add_junctures(self, input_word):
		# Junctures already added?
		if '*' in input_word:
			return input_word
		# Junctures have not been added.
		# Have bookends been added? Remove them.
		if input_word.startswith('#'):
			input_word = input_word[1:]
		if input_word.endswith('#'):
			input_word = input_word[:-1]
		# Add junctures.
		input_word = ''.join([ch + '*' for ch in input_word])[:-1] # Remove last asterisk, lol.
		# Put back bookends.
		input_word = '#{}#'.format(input_word)

		return input_word

	# Given a dict of string labels (describing a strategy) mapped to candidates
	# arrived at via that strategy, print.
	def simple_print(self, results, ground_truth=''):
		from collections.abc import Iterable		
		if not isinstance(results, Iterable) and results in ERRORS:
			print('{}: {}'.format(results, ERRORS[results]))
			return
		if ground_truth == '':
			for result in results:
				print('{}: {}'.format(result, results[result]))
			return
		for result in results:
			evaluation = 'CORRECT' if results[result].pronunciation == ground_truth else 'incorrect'
			print('{}: {}, {}'.format(result, results[result], evaluation))
		print('Ground truth: {}'.format(ground_truth))

	def __init__(self, path="Preprocessing/Out/output.txt", verbose=False):
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			# Determine syllable breaks from each word's encoding.
			# R1: [<>] denotes [<|>]
			# R2: [<digit] denotes [<|digit]
			# R3: [digit>] denotes [digit|>]
			# R4: [digit digit] denotes [digit|digit]
			boundaries = set(['<>', '<0', '<1', '<2', '0>', '1>', '2>', \
				'00', '01', '02', '10', '11', '12', '20', '21', '22'])
			boundary_count = 0
			juncture_count = 0
			for line in f:
				junctured_key = '' # Every juncture will be a *.
				junctured_entry = '' # Junctures will be * or |.
				line = line.split()
				letters = line[0]
				encoding = line[2]
				if len(letters) != len(encoding):
					print('Error: mapping between {} and {} is not 1-to-1.'.format(letters, encoding))
					continue
				# Stats
				# Iterate up to the second-to-last character (we will look ahead by 1 index)
				for i in range(len(letters) - 1):
					# Add char before potential boundary.
					junctured_key += letters[i]
					junctured_entry += letters[i]
					# Add juncture POSSIBILITY to key.
					junctured_key += '*'
					# Determine whether a syllable boundary actually exists.
					potential_boundary = encoding[i] + encoding[i + 1]
					if potential_boundary in boundaries:
						junctured_entry += '|'
						boundary_count += 1
					else:
						junctured_entry += '*'
					juncture_count += 1
				# Add the last letter.
				junctured_key += letters[-1]
				junctured_entry += letters[-1]
				# Bookend with start and end chars.
				junctured_key = '#{}#'.format(junctured_key)
				junctured_entry = '#{}#'.format(junctured_entry)
				# Add entry.
				self.lexical_database[junctured_key] = junctured_entry
				# Precalculate substrings.
				self.substring_database[junctured_key] = [[junctured_key[i:j] for j in range(i, len(junctured_key) + 1) \
					if j - i > 1] for i in range(0, len(junctured_key) - 1)]
				if verbose:
					print('{}\n{}\n{}\n\n'.format(junctured_key, junctured_entry, self.substring_database[junctured_key]))
			if verbose:
				# M&D logged 24.38% for this figure.
				print('{} boundaries out of {} junctures ({:.2f}%)'.format(boundary_count, juncture_count, 100*boundary_count/juncture_count))

sba = SyllabifierByAnalogy()

#sba.cross_validate_syllabify('test', verbose=True)
#sba.cross_validate_syllabify('testing', verbose=True)
#sba.cross_validate_syllabify('mandatory', verbose=True)
#sba.cross_validate_syllabify('authoritative', verbose=True)
#sba.cross_validate_syllabify('national', verbose=True)
#sba.cross_validate_syllabify('stationery', verbose=True)
sba.cross_validate(36645)