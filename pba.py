# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?

class PronouncerByAnalogy:

	class PronunciationLattice:

		class Node:
			def __init__(self, matched_letter, phoneme, index):
				self.matched_letter = matched_letter
				self.phoneme = phoneme
				self.index = index
				self.from_arcs = [] 
				self.to_arcs = []

			def __eq__(self, other):
				if not isinstance(other, type(self)):
					return NotImplemented
				return self.matched_letter == other.matched_letter \
				and self.phoneme == other.phoneme \
				and self.index == other.index

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

		def __init__(self, letters):
			self.letters = letters

			self.nodes = []
			self.arcs = []

			self.start = self.Node('#', '$', None)
			self.end = self.Node('#', '$', None)

		def __str__(self):
			s = ''
			for arc in self.arcs:

				inter_letters = ''
				if arc.from_node != None and arc.to_node != None \
				and arc.from_node.index != None and arc.to_node.index != None:
					inter_letters = self.letters[arc.from_node.index + 1:arc.to_node.index]
					inter_letters = '[' + inter_letters + ']' if inter_letters != '' else ''

				inter = arc.intermediate_phonemes
				if arc.intermediate_phonemes == '' or arc.intermediate_phonemes == None:
					inter = ''
				key = '{}{}{}'.format(arc.from_node.matched_letter, inter_letters, arc.to_node.matched_letter)
				val = '{}{}{}'.format(arc.from_node.phoneme, inter, arc.to_node.phoneme)

				s += '{} [{}, {}] is pronounced {}: {} times\n'.format(key, arc.from_node.index, arc.to_node.index, val, arc.count)
			return s

		def add_or_iterate(self, arc):
			found = False
			for a in self.arcs:
				if arc == a:
					found = True
					a.count += 1
					return
			if not found:
				self.arcs.append(arc)
				if arc.from_node not in self.nodes:
					self.nodes.append(arc.from_node)
				if arc.to_node not in self.nodes:
					self.nodes.append(arc.to_node)

		def add(self, sub_letters, sub_phones, start_index):
			end_index = start_index + len(sub_letters) - 1
			a = self.Node(sub_letters[0], sub_phones[0], start_index)
			b = self.Node(sub_letters[-1], sub_phones[-1], end_index)
			arc = self.Arc(sub_phones[1:-1], a, b)
			self.add_or_iterate(arc)
			# Pair to border nodes if applicable.
			is_start = (start_index == 0)
			is_end = (end_index == len(self.letters) - 1)
			if is_end:
				self.add_or_iterate(self.Arc(None, b, self.end))
			if is_start:
				self.add_or_iterate(self.Arc(None, self.start, a))

	def __init__(self, path="Preprocessing/Out/output.txt"):
		# Assign Lexical Database.
		self.lexical_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			for line in f:
				line = line.split()
				self.lexical_database[line[0]] = line[1]
				print('{}: {}'.format(line[0], line[1]))

	def pronounce(self, input_word):
		# Construct lattice.
		pl = self.PronunciationLattice(input_word)
		# Match Patterns.
		for entry_word in self.lexical_database:
			pronunciation = self.lexical_database[entry_word]
			length_difference = len(input_word) - len(entry_word)
			start_offset = 0
			# a is always the longer word.
			a, b = (input_word, entry_word) if length_difference >= 0 else (entry_word, input_word)
			for i in range(abs(length_difference) + 1):
				match_string = ''
				match_phone = ''
				match_indices = ''
				# Find common substring.
				# Iterate over letters in the shorter word.
				for j, char in enumerate(b):
					if char == a[j]:
						match_string += char
						# When the entry word is smaller, pronunciation needs to shift right to remain accurate.
						match_phone += pronunciation[j + i] if length_difference < 0 else pronunciation[j]
						# When the entry word is bigger, matched indices need to be shifted right to remain accurate.
						match_indices += str(j) + ',' if length_difference < 0 else str(j + i) + ',' # Add comma for 10+ letter words.
					else:
						match_string += ' '
						match_phone += ' '
						match_indices += ' '
				match_strings = match_string.split()
				match_phones = match_phone.split()
				match_indices = match_indices.split()
				match_strings = [m for m in match_strings if len(m) > 1]
				match_phones = [m for m in match_phones if len(m) > 1]
				match_indices = [m for m in match_indices if len(m) > 2] # Account for comma.
				# Add each phoneme to lattice.
				for j, substring in enumerate(match_strings):
					# Add the substring, its phonemes, and the substring's starting index.
					# Add to lattice.
					index_start = int(match_indices[j].split(',')[0])
					pl.add(substring, match_phones[j], index_start)
				# Iterate reference point if input word is the bigger word.
				start_offset += 1 if a == input_word else 0
				a = a[1:]
		print(pl)
pba = PronouncerByAnalogy()
#pba.pronounce('definite')
pba.pronounce('QQQQstrengthQQQQ')