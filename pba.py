# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
global DEBUG
DEBUG = False
class PronouncerByAnalogy:
	# A representation of possible pronunciations of a word.
	class PronunciationLattice:
		# Nodes are endpoints within the target word with a set location and candidate phoneme pronunciation.
		class Node:
			def __init__(self, matched_letter, phoneme, index):
				self.matched_letter = matched_letter
				self.phoneme = phoneme
				self.index = index
				self.from_arcs = [] 
				self.to_arcs = []
				self.visited = False
			def __hash__(self):
				return hash((self.matched_letter, self.phoneme, self.index))
			def __eq__(self, other):
				if not isinstance(other, type(self)):
					return NotImplemented
				return self.matched_letter == other.matched_letter \
				and self.phoneme == other.phoneme \
				and self.index == other.index
			def __ne__(self, other):
				return not self.__eq__(other)
			def __str__(self):
				return '{}'.format(self.phoneme)
		# Arcs span nodes with phonemes between them (or nothing, if the two nodes are bigrams.)
		class Arc:
			def __init__(self, intermediate_phonemes, from_node, to_node):
				self.from_node = from_node
				self.intermediate_phonemes = intermediate_phonemes
				self.to_node = to_node
				self.count = 1
			def __eq__(self, other):
				if not isinstance(other, type(self)):
					return NotImplemented
				return self.from_node == other.from_node \
				and self.intermediate_phonemes == other.intermediate_phonemes \
				and self.to_node == other.to_node
			def __ne__(self, other):
				return not self.__eq__(other)
			def __str__(self):
				return '[{}:{}]'.format(self.intermediate_phonemes, self.count)

		class Candidate:
			# Initialize candidate as empty or as shallow copy.
			def __init__(self, other=None):
				# Init as empty.
				if other == None:
					self.path = [] # Includes all nodes.
					self.arcs = [] # Arcs only.
					# path_strings need to remain fluid during the breadth-first search, because 
					# to "pop" an arc involves the removal of any number of intermediate phonemes.
					self.path_strings = []
					# path_strings get merged into pronunciation after path is completed.
					self.pronunciation = ''
					self.arc_count_sum = 0
					self.arc_count_product = 1
					self.sum_of_products = 0
					self.frequency_of_same_pronunciation = 1 # There's at least one with this pronunciation -- itself.
					self.length = 0
					return
				# Init as shallow copy.
				# Path and path string.
				self.path = other.path[:]
				self.arcs = other.arcs[:]
				self.path_strings = other.path_strings[:]
				self.pronunciation = other.pronunciation
				# Heuristics.
				self.length = other.length
				self.arc_count_sum = other.arc_count_sum
				self.arc_count_product = other.arc_count_product
				self.sum_of_products = other.sum_of_products
				self.frequency_of_same_pronunciation = other.frequency_of_same_pronunciation
			# Finalizes path_strings (only run this when a path is complete.)
			def solidify(self):
				self.pronunciation = ''.join(self.path_strings)

			def __str__(self):
				return '{}: length {}, score {}'.format(''.join(self.pronunciation), self.length, self.score)

			# Append arc to this candidate with its nodes and heuristics.
			def update(self, arc):
				# Update path and path string.
				self.path += [arc.from_node, arc]
				self.arcs += [arc]
				self.path_strings += [arc.from_node.phoneme, arc.intermediate_phonemes]
				# Update heuristics.
				self.arc_count_sum += arc.count
				self.arc_count_product *= arc.count
				self.length += 1
				# If it's the start, we don't need the first node, which merely represents the start node.
				if len(self.arcs) == 1:
					self.path = self.path[1:]
					self.path_strings = self.path_strings[1:]

			def pop(self):
				# Decrement from heuristics.
				self.arc_count_sum -= self.arcs[-1].count
				self.arc_count_product /= self.arcs[-1].count
				self.length -= 1
				# Pop from path and path string.
				self.arcs = self.arcs[:-1]
				self.path = self.path[:-2] # path and path_strings had [node, arc, node], three references to remove.
				self.path_strings = self.path_strings[:-2]

		# Initialize pronunciation lattice.
		def __init__(self, letters):
			self.letters = letters

			self.nodes = {}
			self.arcs = {}

			self.start = self.Node('#', '$', -1)
			self.end = self.Node('#', '$', len(letters))
			self.nodes[hash(('#', '$', -1))] = self.start
			self.nodes[hash(('#', '$', len(letters)))] = self.start

			self.unrepresented_bigrams = set()
		# String interpretation of pronunciation lattice (unlinked. use print() for all linked pronunciations.)
		def __str__(self):
			s = ''
			for arc in self.arcs:
				inter_letters = ''
				if arc.from_node.index != None and arc.to_node.index != None:
					inter_letters = self.letters[arc.from_node.index + 1:arc.to_node.index]
					inter_letters = '<' + inter_letters + '>' if inter_letters != '' else ''

				key = '{}{}{}'.format(arc.from_node.matched_letter, inter_letters, arc.to_node.matched_letter)
				val = '{}{}{}'.format(arc.from_node.phoneme, arc.intermediate_phonemes, arc.to_node.phoneme)

				s += '{} [{}, {}] is pronounced {}: {} times\n'.format(key, arc.from_node.index, arc.to_node.index, val, arc.count)
			return s
		# For debugging.
		def print_nodes(self):
			for node in self.nodes:
				print('Node {} has {} arcs into it and {} arcs out of it.'.format(node.matched_letter + node.phoneme + str(node.index), len(node.from_arcs), len(node.to_arcs)))
		# Lists all paths via breadth-first search.
		def find_all_paths(self, print_progress = False):
			import sys
			min_length = sys.maxsize
			
			# Link unrepresented bigrams.
			# fixes the silence problem.
			self.link_unrepresented()

			candidates = []
			def util(u, d, candidate_buffer):
				nonlocal min_length
				u.visited = True
				if u == d:
					if print_progress:
						print(candidate_buffer)
					complete_candidate = self.Candidate(candidate_buffer)
					complete_candidate.solidify()
					candidates.append(complete_candidate) # Append a copy.
					if candidate_buffer.length < min_length:
						min_length = candidate_buffer.length
				elif candidate_buffer.length < min_length:
					for arc in u.to_arcs:
						v = arc.to_node
						candidate_buffer.update(arc) # Append arc to buffer with its nodes and heuristics. 
						if v.visited == False:
							util(v, d, candidate_buffer) # Recur over successor node.
						candidate_buffer.pop() # Wipe candidate buffer.
				u.visited = False # Allow future revisiting.
			# Set visited to False for all.
			for node in self.nodes.values():
				node.visited = False
			candidate_buffer = self.Candidate()
			# Begin breadth-first search listing all paths.
			util(self.start, self.end, candidate_buffer)
			if len(candidates) == 0:
				print('Warning. No paths were found.')
			return candidates

		# Merge by identical pronunciations generating
		# 1) "the maximum frequency of the same pronunciation (FSP) within the shortest paths," and
		# 2) "the sum of products over...multiple paths [of] identical pronunciations"
		def merge_by_pronunciation(self, candidate_list):
			unique_candidate_list = []
			# Keep a dict of pronunciations and their indices within the new, UNIQUE list of candidates.
			pronunciation_to_index_map = {}
			for i, candidate in enumerate(candidate_list):
				# Has this pronunciation been found before?
				previous_occurrence = pronunciation_to_index_map.get(candidate.pronunciation, -1)
				# First occurrence.
				if previous_occurrence == -1:
					# Account for its own product within the sum_of_products.
					candidate.sum_of_products += candidate.arc_count_product
					# Append reference.
					unique_candidate_list.append(candidate)
					# Map this pronunciation to the index that accesses the unique reference with that pronunciation.
					pronunciation_to_index_map[candidate.pronunciation] = len(unique_candidate_list) - 1

					continue
				# Has been found before. Merge.
				index_of_prev_occurrence = pronunciation_to_index_map[candidate.pronunciation]
				# Update the original's sum_of_products. 
				unique_candidate_list[index_of_prev_occurrence].sum_of_products += candidate.arc_count_product
				# Iterate frequency of same pronunciation.
				unique_candidate_list[index_of_prev_occurrence].frequency_of_same_pronunciation += 1
			return unique_candidate_list

		def decide(self, candidates, verbose=False):
			from operator import attrgetter
			# I will explain this very clearly for my future self.
			# PART 1:
			# - func is a function, either min() or max().
			# - func expects a list of objects and some attribute of that object
			#   by which to sort the list. 
			# - It returns only one candidate (again, either min or max attribute).
			# PART 2:
			# - But what if there are ties for min or max?
			# - The second part filters the list by the min or max attribute.
			# - The entire function, func_by_attribute, returns the list of ties, if applicable.
			def func_by_attribute(list_, attribute, func):
				func_string = ''
				if func == min:
					func_string = 'min'
				elif func == max:
					func_string = 'max'
				else:
					print('Warning. Function {} has not been tested and cannot be guaranteed to work'.format(func))

				# Find min or max attribute among a list of candidates.
				candidate = func(list_, key=attrgetter(attribute))
				attr_val = getattr(candidate, attribute)
				# Filter the candidates by that attribute value.
				filtered_list = list(filter(lambda x: getattr(x, attribute) == attr_val, list_))
				if verbose:
					print('{a} {b}: {c}.\n Candidates of {a} {b}: {d}'.format(a=func_string, b=attribute, c=attr_val, \
						d=[choice.pronunciation for choice in filtered_list]))
				return filtered_list

			if len(candidates) == 0:
				print('Candidates list is empty.')
				return
			
			# Find the minimum length among the candidates
			#min_length = min(candidates, key=attrgetter('length')).length
			# Filter out the candidates by that length.
			#min_lengths = list(filter(lambda x: x.length == min_length, candidates))
			min_lengths = func_by_attribute(candidates, 'length', min)

			if len(min_lengths) == 1:
				# Convert to strings.
				min_lengths = [choice.pronunciation for choice in min_lengths]
				return min_lengths

			unique_candidates = self.merge_by_pronunciation(min_lengths)
			# Supposedly superior selection method.
			max_sum_of_products = func_by_attribute(unique_candidates, 'sum_of_products', max)
			# Old selection method.
			max_scores = func_by_attribute(unique_candidates, 'arc_count_sum', max)

			# Compare old and new method
			if max_scores != max_sum_of_products:
				print('OLD METHOD: {}'.format([item.pronunciation for item in max_scores]))
				print('NEW METHOD: {}'.format([item.pronunciation for item in max_sum_of_products]))

			if len(max_scores) > 1:
				print('There was a tie between {} scores.'.format(len(max_scores)))

			# Convert to strings.
			max_sum_of_products = [choice.pronunciation for choice in max_sum_of_products]
			return max_sum_of_products

		def print(self):
			self.find_all_paths(True)

		def add(self, sub_letters, sub_phones, start_index):
			def create_or_iterate_arc(inter, a, b):
				new = self.Arc(inter, a, b)
				found = self.arcs.get(hash((inter, a, b)), None)
				if found is not None:
					found.count += 1
					return found
				self.arcs[hash((inter, a, b))] = new # Not found. Add new one.
				found2 = self.arcs.get(hash((inter, a, b)), None)
				a.to_arcs.append(new)
				b.from_arcs.append(new)
				return new				# Return.
				
			def create_or_find_node(l, p, i):
				new = self.Node(l, p, i)
				found = self.nodes.get(hash((l, p, i)), None)
				if found is not None:
					return found # Found. Return.

				self.nodes[hash((l, p, i))] = new # Not found. Add new one.
				return new 	# Return it.
			
			# Add start node.
			a = create_or_find_node(sub_letters[0], sub_phones[0], start_index)
			# Add end node.
			b = create_or_find_node(sub_letters[-1], sub_phones[-1], start_index + len(sub_letters) - 1)
			# Add arc between them.
			arc = create_or_iterate_arc(sub_phones[1:-1], a, b)
			# Handle beginning and ending nodes.
			if start_index == 0:
				start_arc = create_or_iterate_arc('', self.start, a)
			elif start_index + len(sub_letters) == len(self.letters):
				end_arc = create_or_iterate_arc('', b, self.end)

		# Adds nodes between gaps in paths to solve the "silence problem."
		def link_unrepresented(self):
			if not len(self.unrepresented_bigrams):
				return
			for item in self.unrepresented_bigrams:
				start_index = item[0]
				end_index = start_index + 1
				bigram = item[1]
				start_char = bigram[0]
				end_char = bigram[1]
				#print('{}: {} at {}, {} at {}'.format(self.letters, start_char, start_index, end_char, end_index))
				# Nodes ending at start_index
				nodes_at_start_index = [node for node in self.nodes.values() if node.index == start_index]
				# Nodes starting at end_index
				nodes_at_end_index = [node for node in self.nodes.values() if node.index == end_index]
				# Because we're iterating from left onward, we know nodes_at_start_index must be populated.
				if not len(nodes_at_start_index):
					# This will only be a problem if the input has not been sanitized.
					print('No nodes started with {}.'.format(start_char))
					exit()
				# Nodes at end index, however, cannot be guaranteed to exist.
				if not len(nodes_at_end_index):
					nodes_at_end_index.append(self.Node(end_char, '-', end_index))

				# Now link all nodes at start to nodes at end through new arcs.
				for start_node in nodes_at_start_index:
					for end_node in nodes_at_end_index:
						self.add(start_node.matched_letter + end_node.matched_letter, \
							start_node.phoneme + end_node.phoneme, start_index)

		# Solves the "silence problem" as documented by M&D in
		# "Can syllabification improve pronunciation by analogy of English?"
		# The silence problem occurs when a letter pair in the input word
		# does not exist in the dataset.
		def flag_unrepresented_bigrams(self, input_word, database):
			represented_bigrams = set()
			keys = list(database.keys())
			# For each word.
			for word in keys:
				# For each bigram.
				for index in range (0, len(word) - 2):
					bigram = word[index] + word[index + 1]
					represented_bigrams.add(bigram)
			unrepresented_bigrams = []
			for x in range(0, len(input_word) - 2):
				bigram = input_word[x] + input_word[x + 1]
				if bigram not in represented_bigrams:
					unrepresented_bigrams.append((x, bigram))

			self.unrepresented_bigrams = unrepresented_bigrams

	def cross_validate(self, start=0):
		prev_time = time.time()
		correct_count = 0
		incorrect_count = 0
		no_paths_found = 0
		total = 0
		trial = start
		trial_count = len(self.lexical_database) - 1
		trial_word = ''
		ground_truth = ''
		while trial < trial_count:
			partial_database = {}
			i = 0
			skipped = False
			
			keys = list(self.lexical_database.keys())

			# Skip short words.
			if len(keys[trial]) <= 2:
				skipped = True
				print('Skipping {} because it\'s too short.'.format(keys[trial]))
				trial += 1
				continue

			trial_word = keys[trial]
			print('Loading trial #{}: {}...'.format(trial, trial_word))
			ground_truth = self.lexical_database[trial_word]
			best, correct = self.cross_validate_pronounce(trial_word)
			incorrect_count += 1 if (not correct) else 0
			correct_count += 1 if correct else 0
			trial += 1
			total += 1
			print('{} / {} ({}%) Correct'.format(correct_count, total, 100*correct_count/total))

			print('Guess: {}\nGround truth: {}'.format(best, ground_truth))
			#print('{} vs. {}'.format(ground_truth, best[0]))
			prev_time = time.time()
			print()

	def __init__(self, path="Preprocessing/Out/output.txt"):
		print('Loading lexical database...')
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			for line in f:
				# Add # and $.
				line = line.split()
				line[0] = '#{}#'.format(line[0])
				line[1] = '${}$'.format(line[1])
				self.lexical_database[line[0]] = line[1]
				self.substring_database[line[0]] = [[line[0][i:j] for j in range(i, len(line[0]) + 1) \
					if j - i > 1] for i in range(0, len(line[0]) + 1)]

	# Removes input word from the dataset before pronouncing if present.
	def cross_validate_pronounce(self, input_word, verbose=False):
		if not input_word.startswith('#'):
			input_word = '#' + input_word
		if not input_word.endswith('#'):
			input_word = input_word + '#'

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
		choices = self.pronounce(input_word, (trimmed_lexical_database, trimmed_substring_database), False)
		if verbose and not found:
			print('Here\'s what pba came up with anyway: {}'.format(choices))
		elif verbose and found:
			print('pba\'s guess: {}'.format(choices))

		if choices:
			return choices, (answer in choices)
		return choices, False

	def pronounce(self, input_word, trimmed_databases=None, verbose=False):
		# Default to the database loaded in the constructor.
		lexical_database = self.lexical_database
		substring_database = self.substring_database

		# Refer to pruned versions when called by cross_validate_pronounce.
		if trimmed_databases != None:
			lexical_database = trimmed_databases[0]
			substring_database = trimmed_databases[1]
		if verbose:
			print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		pl = self.PronunciationLattice(input_word)

		# Bigrams unrepresented in the dataset will cause gaps in lattice paths.
		pl.flag_unrepresented_bigrams(input_word, lexical_database)

		# Second fastest.
		# The original method of Dedina and Nusbaum. Words begin left-aligned and end right-aligned.
		def populate_legacy():
			nonlocal input_word
			nonlocal entry_word
			nonlocal phonemes
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
							pl.add(match, phonemes[index + offset : index + offset + length], index)
						else:
							# When the entry word is smaller, matched indices "shift right" to remain accurate.
							pl.add(match, phonemes[index : index + length], index + offset)
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
				substr, i = substr_index_tuple
				indices_in_bigger = [m.start() for m in re.finditer('(?={})'.format(substr), bigger_w)]
				# Add to the lattice.
				for bigger_index in indices_in_bigger:
					# Entry word is the bigger word.
					if length_diff <= 0:
						# The smaller word's starting index, then, is i, because of how input_precalculated_substrings are organized.
						# Locate the indices in the entry word out of which to slice the phonemes.
						pl.add(substr, phonemes[bigger_index : bigger_index + len(substr)], i)
					# Input word is the bigger word.
					else:
						pl.add(substr, phonemes[i : i + len(substr)], bigger_index)
			# TODO: Only match upon a break. That way,
			# to,
			# tor,
			# tori,
			# these substrings won't get double counted.
			import re
			nonlocal input_precalculated_substrings
			nonlocal input_word
			nonlocal entry_word
			nonlocal phonemes
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
						# has been accounted for or not. (Imagine a scenario where the very last checked substring
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
			phonemes = lexical_database[entry_word]
			populate_precalculated()
			#populate_legacy()
		if verbose:
			print('Done.')
			print('{} nodes and {} arcs.'.format(len(pl.nodes), len(pl.arcs)))
		candidates = pl.find_all_paths()
		best = pl.decide(candidates)
		if verbose and best is not None:
			print('Best: {}'.format([str(item) for item in best]))
		return best

import time
pba = PronouncerByAnalogy()
#pba.pronounce('autoperambulatorification', verbose=True)
#pba.pronounce('iota')
#pba.cross_validate_pronounce('keyboard', verbose=True)
pba.cross_validate(25000)