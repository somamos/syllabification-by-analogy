# A representation of possible mappings from a word's spelling to some alternate domain (pronunciation or syllabification).

NO_PATHS_FOUND = 999
SEARCHED_TOO_LONG = 998
WORD_TOO_SHORT = 997
ERRORS = { 
999: 'NO_PATHS_FOUND', \
998: 'SEARCHED_TOO_LONG', \
}

class Lattice:
	# Nodes are endpoints within the target word with a set location and candidate phoneme.
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
		def __init__(self, intermediate_phonemes, intermediate_letters, from_node, to_node):
			self.from_node = from_node
			self.intermediate_phonemes = intermediate_phonemes
			self.intermediate_letters = intermediate_letters
			self.to_node = to_node
			self.count = 1
			self.from_words = []
			# Used to assemble what M&D call "path structure."
			self.structure_component = (to_node.index - from_node.index)
		def __eq__(self, other):
			if not isinstance(other, type(self)):
				return NotImplemented
			return self.from_node == other.from_node \
			and self.intermediate_phonemes == other.intermediate_phonemes \
			and self.to_node == other.to_node
		def __ne__(self, other):
			return not self.__eq__(other)
		def __str__(self):
			#if any(self.from_words):
			#	return '\n{}{}{}({}{}{}): {},  (from words {})'.format(self.from_node.phoneme, self.intermediate_phonemes, self.to_node.phoneme, \
			#		self.from_node.matched_letter, self.intermediate_letters, self.to_node.matched_letter, self.count, self.from_words)			
			return '[{}] {}{}{}({}{}{}): {}'.format(self.from_node.index, self.from_node.matched_letter, self.intermediate_letters, self.to_node.matched_letter,\
				self.from_node.phoneme, self.intermediate_phonemes, self.to_node.phoneme, self.count)
		def __hash__(self):
			return hash((self.from_node, self.intermediate_phonemes, self.to_node))
		# Accepts a list of nodes.
		# Returns whether this arc's endpoints exist within that list.
		def contains(self, list_of_nodes):
			return (self.from_node in list_of_nodes) or (self.to_node in list_of_nodes)				

	class Candidate:
		# Initialize candidate as empty or as shallow copy.
		def __init__(self, parent, arcs=None):
			# Init as empty.
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
			self.path_structure_standard_deviation = 0
			self.weakest_link = 0
			self.number_of_different_symbols = 0
			if arcs == None:
				return
			for arc in arcs:
				self.update(parent, arc)
			self.solidify()
		# Finalizes path_strings (only run this when a path is complete.)
		def solidify(self):
			self.pronunciation = ''.join(self.path_strings)
		def __eq__(self, other):
			if not isinstance(other, type(self)):
				return NotImplemented
			return self.pronunciation == other.pronunciation
		def __ne__(self, other):
			return not self.__eq__(other)
		def __str__(self):
			return self.pronunciation
		def __hash__(self):
			return hash(tuple([arc for arc in self.arcs]))
		# Append arc to this candidate with its nodes and heuristics.
		def update(self, parent, arc):
			# Update path and path string.
			self.path += [arc.from_node, arc]
			self.arcs += [arc]
			self.path_strings += [arc.from_node.phoneme, arc.intermediate_phonemes]
			# Update heuristics.
			# Ignore start node and end node's counts. Those arcs would only count how many times a word starts with
			# the word's start letter and ends with the word's end letter.
			self.arc_count_sum += arc.count if not arc.contains([parent.START_NODE, parent.END_NODE]) else 0
			self.length += 1
			# If it's the start, we don't need the first node, which merely represents the start node.
			if len(self.arcs) == 1:
				self.path = self.path[1:]
				self.path_strings = self.path_strings[1:]

		def pop(self, parent):
			# Decrement from heuristics.
			removed = self.arcs[-1]
			self.arc_count_sum -= removed.count if not removed.contains([parent.START_NODE, parent.END_NODE]) else 0
			self.length -= 1
			# Pop from path and path string.
			self.arcs = self.arcs[:-1]
			self.path = self.path[:-2] # path and path_strings had [node, arc, node], three references to remove.
			self.path_strings = self.path_strings[:-2]

	# Initialize pronunciation lattice.
	# Breadth-first search will print # candidate paths every ITERATIONS_PER_PRINT. 
	# Breadth-first search will give up after QUIT_THRESHOLD recurrences.
	# The default values are tuned to terminate the dataset's longest word, "supercalifragilisticexpialidocious,"
	# after a couple of minutes.
	def __init__(self, letters, ITERATIONS_PER_PRINT=25000, QUIT_THRESHOLD=1000000):
		self.letters = letters
		self.ITERATIONS_PER_PRINT = ITERATIONS_PER_PRINT
		self.QUIT_THRESHOLD	= QUIT_THRESHOLD

		self.nodes = {}
		self.arcs = {}

		self.START_NODE = self.Node('', '', -1)
		self.END_NODE = self.Node('', '', len(letters))
		self.nodes[hash(('', '', -1))] = self.START_NODE
		self.nodes[hash(('', '', len(letters)))] = self.END_NODE

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

	def find_all_paths(self, verbose = False):
		from collections import deque
		import time
		time_before = time.perf_counter()
		
		furthest_index = 0
		overflow = False
		
		def bfs(start, end):
			import sys
			iter_count = 0
			min_length = sys.maxsize
			nonlocal overflow
			nonlocal furthest_index

			queue = deque([([start], [])])  # Each item in the queue is a tuple (nodes, arcs)
			paths = []
			while queue:
				# Avoid searching for too long.
				if iter_count != 0 and iter_count%self.ITERATIONS_PER_PRINT == 0:
					print('Iterated {} times. {} paths found.'.format(iter_count, len(paths)))
				iter_count += 1
				if iter_count > self.QUIT_THRESHOLD:
					overflow = True
					return

				nodes, arcs = queue.popleft()
				node = nodes[-1]
				furthest_index = node.index if node.index > furthest_index else furthest_index

				if node == end:
					min_length = len(arcs)
					paths.append(arcs)
				elif len(arcs) + 1 > min_length:
					continue
				for arc in node.to_arcs:
					neighbor = arc.to_node
					if neighbor not in nodes:
						queue.append((nodes + [neighbor], arcs + [arc]))
			return paths

		prev_furthest_index = -1
		while (furthest_index < len(self.letters)):
			paths = bfs(self.START_NODE, self.END_NODE)
			# Various error handling:
			if furthest_index == prev_furthest_index:
				print('Progress has stopped.')
				return NO_PATHS_FOUND
			if overflow:
				return SEARCHED_TOO_LONG
			if len(paths) > 0:
				break
			print('WARNING. No paths found. Attempting to patch gap at index {}:'.format(furthest_index))
			self.link_silences(furthest_index)
			prev_furthest_index = furthest_index

		candidates = []
		if verbose:
			print('CANDIDATES FOUND:')
		for path in paths:
			candidates.append(self.Candidate(self, path))
			if verbose:
				print("{}, length: {}".format(candidates[-1].pronunciation, len(candidates[-1].arcs)))

		duration = time.perf_counter() - time_before
		print('Found {} paths in {} seconds'.format(len(candidates), duration))
		return candidates

	# Count identical pronunciations generating
	# 1) "the maximum frequency of the same pronunciation (FSP) within the shortest paths," and
	# 2) "the sum of products over...multiple paths [of] identical pronunciations"
	def get_frequencies_by_pronunciation(self, candidate_list):
		# Map unique pronunciations to the number of times that pronunciation occurs.
		pronunciation_to_repeat_count = {}
		# Map unique pronunciations to the sum of (products of each occurrence's arcs).
		pronunciation_to_sum_of_product = {}
		for i, candidate in enumerate(candidate_list):
			# Iterate frequency.
			pronunciation_to_repeat_count[candidate.pronunciation] = pronunciation_to_repeat_count.get(candidate.pronunciation, 0) + 1
			# Add sum of products.
			pronunciation_to_sum_of_product[candidate.pronunciation] = \
				pronunciation_to_sum_of_product.get(candidate.pronunciation, 0) + candidate.arc_count_product
		return pronunciation_to_repeat_count, pronunciation_to_sum_of_product

	# These help break ties. See page 9 of "Can syllabification improve pronunciation by analogy of English?"
	def compute_heuristics(self, candidates):
		import math
		import statistics
		from operator import attrgetter
		# 1. Maximum arc count product
		for i in range(len(candidates)):
			candidates[i].arc_count_product = math.prod([arc.count for arc in candidates[i].arcs])

		pronunciation_to_repeat_count, pronunciation_to_sum_of_product = self.get_frequencies_by_pronunciation(candidates)

		other_candidates_symbols = ''
		for i in range(len(candidates)):
			pronunciation = candidates[i].pronunciation
			# 2. Minimum standard deviation.
			candidates[i].path_structure_standard_deviation = statistics.stdev([arc.structure_component for arc in candidates[i].arcs])
			#print('{}: {}'.format([arc.intermediate_phonemes for arc in self.arcs], self.path_structure_standard_deviation))

			# 3. Maximum frequency of the same pronunciation 
			candidates[i].frequency_of_same_pronunciation = pronunciation_to_repeat_count[pronunciation]
			# (We'll also do sum of products here, too, even though it's not one of M&D's 5.)
			candidates[i].sum_of_products = pronunciation_to_sum_of_product[pronunciation]

			# 4. Minimum number of different symbols per candidate.
			number_of_different_symbols = 0
			# Isolate current candidate from others.
			other_candidates = candidates[:i] + candidates[i + 1:]
			# Compare char at each index of this candidate to that of every competitor, counting differences.
			for other_candidate in other_candidates:
				for j, ch in enumerate(pronunciation):
					number_of_different_symbols += 1 if ch != other_candidate.pronunciation[j] else 0
			candidates[i].number_of_different_symbols = number_of_different_symbols
			#print('{} different symbols in {} versus {}'.format(number_of_different_symbols, candidates[i], other_candidates_symbols))

			# 5. Maximum weakest link. (The weakest link is the minimum arc count)
			candidates[i].weakest_link = min([arc.count for arc in candidates[i].arcs if not arc.contains([self.START_NODE, self.END_NODE])])

		#print(['{}: {}'.format(arc.from_node.matched_letter + arc.intermediate_phonemes + arc.to_node.matched_letter, arc.count) for arc in self.arcs])

	# Ranks candidates by the five heuristics. 
	def rank_by_heuristics(self, candidates):
		import itertools
		# Rank according to these five heuristics and orders.
		heuristic = ['arc_count_product', \
			'path_structure_standard_deviation', \
			'frequency_of_same_pronunciation', \
			'number_of_different_symbols', \
			'weakest_link']
		descending = [True, False, True, False, True]

		results = tuple([self.rank_by_heuristic(candidates, heuristic[i], \
			descending=descending[i], verbose=False) for i in range(len(heuristic))])
		# We pass in heuristic[i] for titling print statements only.
		results = tuple([self.rank_to_score(leaderboard, heuristic[i]) for i, leaderboard in enumerate(results)])

		labeled_results = {}
		# Rank fusion.
		# There are 31 possible rank fusions, i.e.:
		# 00001, 00011, 00101, ..., 10111, 01111, 11111
		strategies = list(itertools.product([0, 1], repeat=5))
		# Permute through every way of scoring.
		for strategy in strategies:
			# Ignore 00000.
			if not any(strategy):
				continue
			label = '' # A string representation of this fusion.
			# Flush dict for this current fusion method.
			totals = {}
			# Each bit maps onto a results column, multiplied by the bit.
			for i, bit in enumerate(strategy):
				label += str(bit)
				if not bit:
					continue
				column = results[i]
				for candidate in candidates:
					# Multiply by points received by this strategy, or 1 if this strategy is not included
					# (though technically that triggers continue above.)
					totals[candidate] = totals.get(candidate, 1) * (column[candidate] * bit + (1 - bit))
			# Now that every column has been added, save the maximum.
			best = max(totals, key=totals.get)
			best_val = totals[best]
			#print(label)
			#print('{}: {}'.format(best.pronunciation, best_val))
			labeled_results[label] = best
		return labeled_results

	# The best rank is 1. Then 2, then 3, and so on.
	# Multiple candidates can share the same rank, naturally.
	def rank_by_heuristic(self, candidates, attribute, descending=True, verbose=False):
		from operator import attrgetter
		candidates.sort(key=attrgetter(attribute), reverse=descending)
		# Map candidates to how well they did (lower is better.)
		candidate_to_rank_map = {}
		# Sort candidates by attribute.
		prev = getattr(candidates[0], attribute)
		rank = 1
		# Ties within one rank should increase the gap between that rank and the next.
		candidates_at_prev_rank = 0 	# i.e. 1st, 1st, 1st, 2nd, 3rd -> 1st, 1st, 1st, 4th, 5th
		# Every time the attribute changes, we increment the score.
		for candidate in candidates:
			curr = getattr(candidate, attribute)
			if prev != curr:
				# The next tier has been reached.
				rank += candidates_at_prev_rank
				candidates_at_prev_rank = 0
			candidate_to_rank_map[candidate] = rank
			candidates_at_prev_rank += 1
			prev = curr
		if verbose:
			print('Ranked candidates by {}. Results:\n'.format(attribute))
			for key in candidate_to_rank_map.keys():
				print('#{}: {} ({})'.format(candidate_to_rank_map[key], key.pronunciation, getattr(key, attribute)))
		return candidate_to_rank_map

	# Given a dict of candidates mapped to their rank given some heuristic,
	# Distribute points.
	# Return a dict of candidates mapped to points received.
	def rank_to_score(self, candidate_to_rank_map, heuristic, verbose=False):
		candidate_to_score_map = {}
		# Total points awarded: N(N + 1)/2 where N is the number of candidates.
		# Handling ties:
		# For a given range of tied candidates, we evenly distribute the number 
		# of points that would have been awarded had there been no ties within that range.
		# CANDIDATE RANK----1---2---3---3---3---6---7
		# POINTS, NO TIES---7---6--[5---4---3]--2---1
		# POINTS WITH TIES--7---6--[4---4---4]--2---1
		points_awarded_to_first = len(candidate_to_rank_map) # Points awarded to first place if not tied.

		rank_to_points_map = {}
		point_buffer = 0
		candidates_at_this_rank = 0
		# Thankfully, dict order is preserved. We can count on the first entry being rank 1.
		prev_rank = -1
		# Map each rank to the number of points awarded to that rank.
		for n, rank in enumerate(candidate_to_rank_map.values()):
			if prev_rank != rank:
				# Rank has just changed. Flush the buffer.
				point_buffer = points_awarded_to_first - n
				candidates_at_this_rank = 1
			else:
				# Points will be shared evenly between these iterations' candidates.
				point_buffer += points_awarded_to_first - n
				candidates_at_this_rank += 1
			# Update mapping.
			rank_to_points_map[rank] = point_buffer/candidates_at_this_rank
			# Prepare to iterate.
			prev_rank = rank
		if verbose:
			print('Points awarded to candidates for {}:'.format(heuristic))
		# Distribute the points to each rank.
		for candidate in candidate_to_rank_map:
			rank = candidate_to_rank_map[candidate]
			points = rank_to_points_map[rank]
			if verbose:
				print('{}, rank {}, got {} points'.format(candidate.pronunciation, rank, points))
			candidate_to_score_map[candidate] = points
		return candidate_to_score_map
	# Given a list of pronunciation candidates, returns a dict of string labels mapped to either:
	# 1) the shortest path candidate, if a unique shortest path exists.
	# 2) 31 candidates determined by every posisble fusion of 5 heuristics, 
	#    as well as 2 candidates chosen by "simple" single-strategies.
	def decide(self, candidates, verbose=False):
		from operator import attrgetter
		from collections.abc import Iterable
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
			from collections.abc import Iterable
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
		if candidates == None:
			print('Candidates list is None.')
			return
		elif not isinstance(candidates, Iterable) and candidates in ERRORS:
			print('Error reached.')
			return candidates # This is an error code.
		elif len(candidates) == 0:
			print('Candidates list is empty.')
			return

		
		# Find the minimum length among the candidates
		#min_length = min(candidates, key=attrgetter('length')).length
		# Filter out the candidates by that length.
		#min_lengths = list(filter(lambda x: x.length == min_length, candidates))
		min_lengths = func_by_attribute(candidates, 'length', min)

		if len(min_lengths) == 1:
			# Convert to strings.
			return {'min_length': min_lengths[0]}

		self.compute_heuristics(min_lengths)
		results = self.rank_by_heuristics(min_lengths)

		# Choose the 0th of each of the following, just because rank_by_heuristics can't break ties either.
		# Supposedly superior selection method.
		results['sum_of_products'] = func_by_attribute(min_lengths, 'sum_of_products', max)[0]
		# Old selection method.
		results['arc_count_sum'] = func_by_attribute(min_lengths, 'arc_count_sum', max)[0]

		return results
	# Given two lattices a and b,
	# a_only is the set of arcs distinct to a
	# b_only is the set of arcs distinct to b
	# shared is the set of arcs in both a and b
	# given each shared arc s and its diff = (count of s in a) - (count of s in b)
	#	a_shortage is the subset of shared arcs such that diff < 0
	#	a_surplus is the subset of shared arcs such that diff > 0
	#	a_b_unity is the subset of shared arcs such that diff = 0
	@staticmethod
	def print_lattice_comparison(a, b):
		print('LATTICE COMPARISON:')
		unique_to_a, unique_to_b, shared, a_shortage, a_surplus, a_b_unity = [], [], [], [], [], []
		# Populate uniques and shared
		unique_to_a_sum = 0
		unique_to_b_sum = 0
		for hash_ in a.arcs:
			# Arcs not in b.
			if hash_ not in b.arcs:
				unique_to_a_sum += a.arcs[hash_].count
				unique_to_a.append(a.arcs[hash_])
			# Shared arcs.
			else:
				# Shared will be further disambiguated later, so do not factor in its counts yet.
				# Append a tuple of the reference in a and its reference in b.
				shared.append((a.arcs[hash_], b.arcs[hash_]))
		# Arcs not in a.
		for hash_ in b.arcs:
			if hash_ not in a.arcs:
				unique_to_b_sum += b.arcs[hash_].count
				unique_to_b.append(b.arcs[hash_])
		# Sanity check.

		if len(a.arcs) + len(b.arcs) - 2*len(shared) != len(unique_to_a) + len(unique_to_b):
			print('Sanity check failed. {} + {} - 2*{} != {} + {}'.format(len(a.arcs), len(b.arcs), len(shared), len(unique_to_a), len(unique_to_b)))

		print('{} arcs were shared, {} were unique to a, {} were unique to b.'.format(len(shared), len(unique_to_a), len(unique_to_b)))
		a_shortage_sum = 0
		a_surplus_sum = 0
		unity_sum = 0
		# Split shared into a_shortage, a_surplus, and a_b_unity.
		for arc_in_a, arc_in_b in shared:
			diff = arc_in_a.count - arc_in_b.count
			if diff < 0:
				a_shortage_sum += diff
				a_shortage.append((arc_in_a, arc_in_b))
			elif diff > 0:
				a_surplus_sum += diff
				a_surplus.append((arc_in_a, arc_in_b))
			else:
				a_b_unity.append((arc_in_a, arc_in_b))
				unity_sum += arc_in_a.count
		# Sanity check.
		if len(a_shortage) + len(a_surplus) + len(a_b_unity) != len(shared):
			print('Sanity check #2 failed: {} + {} + {} != {}'.format(len(a_shortage), len(a_surplus), len(a_b_unity), len(shared)))
		print('Of the {} shared arcs:\n  {} had fewer counts in a ({}),\n  {} had greater counts in a ({}), and\n  {} had the same counts in both ({})'.format( \
			len(shared), len(a_shortage), a_shortage_sum, len(a_surplus), a_surplus_sum, len(a_b_unity), unity_sum))

		print('COUNT OFFSET:')
		print('unique_to_a_sum: {}, unique_to_b_sum: {}, a_shortage_sum: {}, a_surplus_sum: {}, unity_sum: {}'.format( \
			unique_to_a_sum, unique_to_b_sum, a_shortage_sum, a_surplus_sum, unity_sum))

		out = ''
		out += 'Arcs with greater counts in A:\n'
		out += '\n'.join('  {} vs {}'.format(str(arc[0]), str(arc[1])) for arc in a_surplus) if len(a_surplus) else '  None.'
		out += '\nArcs with fewer counts in A:\n'
		out += '\n'.join('  {} vs {}'.format(str(arc[0]), str(arc[1])) for arc in a_shortage) if len(a_shortage) else '  None.\n'
		print(out)


	def print_arcs(self):
		print('ALL ARCS:')
		for hsh in self.arcs:
			print(str(self.arcs[hsh]))

	def print(self):
		self.find_all_paths(True)

	def create_or_iterate_arc(self, inter, inter_letters, a, b, word='', forced_count=0):
		#print('Given word "{}":'.format(word))
		new = self.Arc(inter, inter_letters, a, b)
		#print('  Looking for arc {} in:\n'.format(new))
		found = self.arcs.get(hash((inter, a, b)), None)
		if found is not None: 
			if forced_count != 0:
				print('Error. Forcing the count of a duplicate arc: {}'.format(str(found)))
				exit()
			# Do not iterate start or end nodes.
			found.count += 1 if not found.contains([self.START_NODE, self.END_NODE]) else 0 # this word's first and end letter.
			found.from_words.append(word)
			return found
		self.arcs[hash((inter, a, b))] = new # Not found. Add new one.
		found2 = self.arcs.get(hash((inter, a, b)), None)
		a.to_arcs.append(new)
		b.from_arcs.append(new)
		new.from_words.append(word)
		# Force count if applicable.
		if forced_count > 1:
			new.count = forced_count
		return new				# Return.
		
	def create_or_find_node(self, l, p, i):
		new = self.Node(l, p, i)
		found = self.nodes.get(hash((l, p, i)), None)
		if found is not None:
			return found # Found. Return.

		self.nodes[hash((l, p, i))] = new # Not found. Add new one.
		return new 	# Return it.

	# Adds phonemes with a precalculated count. Yeah, I could overload add, but multiprocessing 
	# passes in a tuple of arguments with no regard for default arguments' names, and I don't want
	# that to cause issues (like "word" being mistaken for "forced_count" or vice versa).
	def add_forced(self, sub_letters, sub_phones, start_index, forced_count):
		a = self.create_or_find_node(sub_letters[0], sub_phones[0], start_index)
		b = self.create_or_find_node(sub_letters[-1], sub_phones[-1], start_index + len(sub_letters) - 1)
		arc = self.create_or_iterate_arc(sub_phones[1:-1], sub_letters[1:-1], a, b, forced_count=forced_count)
		if start_index == 0:
			start_arc = self.create_or_iterate_arc('', '', self.START_NODE, a)
		if start_index + len(sub_letters) == len(self.letters):
			end_arc = self.create_or_iterate_arc('', '', b, self.END_NODE)

	def add(self, sub_letters, sub_phones, start_index, word=''):
		a = self.create_or_find_node(sub_letters[0], sub_phones[0], start_index) # Local start.
		b = self.create_or_find_node(sub_letters[-1], sub_phones[-1], start_index + len(sub_letters) - 1) # Local end.
		arc = self.create_or_iterate_arc(sub_phones[1:-1], sub_letters[1:-1], a, b, word=word) # Arc between.
		# Handle global beginning and end.
		if start_index == 0:
			start_arc = self.create_or_iterate_arc('', '', self.START_NODE, a)
		if start_index + len(sub_letters) == len(self.letters):
			end_arc = self.create_or_iterate_arc('', '', b, self.END_NODE)

	# Fix the silence problem.
	# Every node at index furthest should link to every node at furthest + 1.
	# If there is no node at a given index, add one.
	def link_silences(self, furthest):
		import re
		# Link every node at index i to every node at index i + 1.
		added_count = 0
		def link(i):
			nonlocal added_count
			furthest_reached_nodes = []
			nodes_beyond = []
			for hash_ in self.nodes:
				if self.nodes[hash_].index == i:
					furthest_reached_nodes.append(self.nodes[hash_])
				elif self.nodes[hash_].index == i + 1:
					nodes_beyond.append(self.nodes[hash_])
			if len(nodes_beyond) == 0:
				# TODO: Get this to work with Syllabification (which does not expect '-')
				nodes_beyond.append(self.Node(self.letters[i + 1], '-', i + 1))
			print('Adding {} x {} arcs'.format(len(furthest_reached_nodes), len(nodes_beyond)))
			for from_node in furthest_reached_nodes:
				for to_node in nodes_beyond:
					self.add(from_node.matched_letter + to_node.matched_letter, \
						from_node.phoneme + to_node.phoneme, i)
					added_count += 1
		# Get the unpaired letters by index.
		silent_pair = self.letters[furthest] + self.letters[furthest + 1]
		# Find every instance of the problematic letters.
		indices = [m.start() for m in re.finditer('(?={})'.format(silent_pair), self.letters)]
		# Patch all instances.
		print('Instances of {}:\n{}'.format(silent_pair, indices))
		for index in indices:
			link(index)
		print('Successfully added {} arcs.'.format(added_count))
