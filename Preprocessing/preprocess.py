# coding: latin-1

# We map phoneme representations defined in dataset a to the ones outlined by Sejnowski and Rosenberg 
# in their 1987 paper "Parallel Networks that Learn to Pronounce English Text."

phoneme_map = \
{
				# FROM		TO 
				# (Example words given in dataset a and S&R's NETTalk paper respectively)
	# VOWELS
	'aa': 'a', 	# _o_dd, 	f_a_ther
	'ay': 'A',	# h_i_de,	b_i_te <--These two are spoken differently for Americans due to Canadian Raising.
	'ao': 'c', 	# _ou_ght,	b_ou_ght  TODO: split them.
	'ae': '@',	# _a_t,		b_a_t
	'ah': '^',	# h_u_t,	b_u_t
	'aw': 'W',	# c_ow_,	b_ou_t
	'iy': 'i',	# _ea_t,	p_e_te
	'ih': 'I',	# _i_t,		b_i_t
	'ow': 'o',	# _oa_t,	b_oa_t
	'oy': 'O',	# t_oy_,	b_oy_
	'eh': 'E',	# _e_d, 	b_e_t
	'er': 'R',	# h_ur_t,	b_ir_d
	'ey': 'e',	# _a_te,	b_a_ke	
	'uh': 'U',	# h_oo_d,	b_oo_k
	'uw': 'u',	# t_wo_,	l_u_te
	# CONSONANTS
	'b': 'b', 	# _b_e, 	_b_et
	'ch': 'C',	# _ch_eese,	_ch_in	
	'd': 'd',	# _d_ee,	_d_ebt
	'dh': 'D',	# _th_ee,	_th_is
	'f': 'f',	# _f_ee,	_f_in
	'g': 'g',	# _g_reen,	_g_uess
	'hh': 'h',	# _h_e,		_h_ead
	'jh': 'J',	# _g_ee,	_g_in
	'k': 'k',	# _k_ey,	_k_en
	'l': 'l',	# _l_ee,	_l_et
	'm': 'm',	# _m_e,		_m_et
	'n': 'n',	# _kn_ee,	_n_et
	'ng': 'G',	# pi_ng_, 	si_ng_
	'p': 'p',	# _p_ee,	_p_et
	'r': 'r',	# _r_ead,	_r_ed
	's': 's',	# _s_ea,	_s_it
	'sh': 'S',	# _sh_e,	_sh_in
	't': 't',	# _t_ea,	_t_est
	'th': 'T',	# _th_eta,	_th_in
	'v': 'v',	# _v_ee,	_v_est
	'w': 'w',	# _w_e,		_w_et
	'y': 'y',	# _y_ield,	_y_et
	'z': 'z',	# _z_ee,	_z_oo
	'zh': 'Z',	# sei_z_ure, lei_s_ure
}

# Dataset a defines 39 phonetic symbols, whereas S&R describe 51. Of the remaining 12, 
# only one cannot be extracted from dataset a. It is /:/, e.g. lo_g_ic, which dataset a treats as identical to jh.
# The other 11 belong to two categories:
# - unmapped, which represent two combined phonemes from the 39.
# - context_dependent, which are unmapped phonemes that can be salvaged from dataset a
#   using (ending) position and (lack of) stress.

unmapped = \
{						# S&R examples:
	# diphthongs		
	'yu': 'Y',	# c_u_te
	'yU': 'Y', # c_U_rate
	'yx': 'Y', # artic_u_lar
	'xl': 'L', # yentl
	'Izxm': 'IzM', # escap_ism_
	# clusters
	'kS': 'K',	# se_x_ual
	'ks': 'X',	# e_xc_ess
	'gz': '#', 	# e_x_amine
	'w^': '*', 	# _o_ne
	'wx': '*',
	'ts': '!',	# na_z_i
	'kw': 'Q'	# _qu_est
}

all_phonemes = list(phoneme_map.values()) + list(unmapped.values())
all_letters = alphabet = [char for char in 'abcdefghijklmnopqrstuvwxyz']

vowel_letters = 'aeiouy'
nuclei = 'aAc@^WiIoOEReUuYx*LM'

'''
# These features described in S&R can be teased out of dataset a given additional context.
context_dependent = \
{
	# TODO: Replace 'END' with the actual character.
	# TODO: Replace the dataset a representations with S&R
									# S&R examples:
	['ah0']: 'x',					# _a_bout
	['xl', 'END']: 'L',		# bott_le_
	['m', 'END']: 'M',				# absy_m_
	['n', 'END']: 'N'				# butto_n_
}
'''

# The representation of a word used by preprocess.py and align.py.
class Word:
	def append_self(self, arr, include_encodings=True):
		if not include_encodings:
			arr.append('{:20} {:20}\n'.format(self.letters, self.phonemes))
			return arr
		arr.append('{:20} {:20} {:20}\n'.format(self.letters, self.phonemes, self.syllable_boundary_encodings))
		return arr

	def __init__(self, letters, phonemes, stresses, unaligned_boundary_buffer=None):
		self.letters = letters
		self.phonemes = phonemes
		self.stresses = stresses
		self.syllable_count = len(stresses)
		self.syllable_boundary_encodings = None # Gets populated later.
		# Additions for dataset c, which (dataset) includes syllable boundaries in the unaligned phoneme domain.
		# We will use this information to infer syllable boundary placement in the letters domain after alignment.
		self.phonemes_unaligned = phonemes
		self.unaligned_boundary_buffer = unaligned_boundary_buffer
		# This gets initialized post-alignment.
		self.boundary_buffer = None
		# "anchor" pre-alignment phoneme nucleus indices to the encodings' nucleus indices.
		self.anchors = []

	# Translate pre-alignment indices to post-alignment ones. 
	# (Return True upon success, False upon failure.)
	# For instance, take the word 'ellipsis.' IlI[p]sIs -> Il-I[p]sIs
	# Its phoneme 'p' at unaligned index 3 now belongs at aligned index 4.
	# We can't just index naively by the phoneme, due to repeat characters.
	# unaligned = IlIpsIs
	# aligned   = Il-IpsIs
	# Whenever the character at unaligned does NOT equal the character at aligned,
	# it must be due to a dash. (if not, print a warning.)
	# iterate aligned until they equal each other again.
	# At every instance unaligned is in the unaligned boundary indices list, push the
	# current aligned index to the aligned boundary indices list.
	def adjust_boundary_indices(self):
		aligned = self.phonemes
		unaligned = self.phonemes_unaligned
		if self.phonemes_unaligned == self.phonemes:
			# No adjustment needed.
			self.boundary_buffer = self.unaligned_boundary_buffer
			return True
		# Initialize boundary buffer.
		self.boundary_buffer = []

		offset = 0
		for i in range(len(self.phonemes_unaligned)):
			while unaligned[i] != aligned[i + offset]:
				# Sanity check.
				if aligned[i + offset] != '-':
					#print('Warning. The lack of alignment is NOT due to a dash. This should never happen.')
					#print('Word: {} Unaligned: {} Aligned: {} index: {} offset: {}'.format(self.letters, unaligned, aligned, i, offset))
					return False
				offset += 1
			if i in self.unaligned_boundary_buffer:
				self.boundary_buffer.append(i + offset)
		#print('{}\'s aligned phonemes: {}, Buffer before alignment: {} After: {}'.format( \
		#	self.letters, aligned, self.unaligned_boundary_buffer, self.boundary_buffer))
		return True

	# For dataset c. Return True upon success, False otherwise.
	def encode_boundaries_post_alignment(self):
		# The number of boundaries between syllables is always 1 less than the syllable count.
		if self.syllable_count != len(self.boundary_buffer) + 1:
			return False
		final_encoding = ''
		index = 0
		reached_nucleus = False
		stresses_reached = 0
		for index, ph in enumerate(self.phonemes):
			if index in self.boundary_buffer: # The previous index marked syllable end.
				reached_nucleus = False # New syllable. Reset nucleus flag.
			# Every character in a syllable "points" to the nucleus.
			if not reached_nucleus:
				# Handle nuclei.
				if ph in nuclei:
					# This is the nucleus. Insert stress level.
					final_encoding += self.stresses[stresses_reached]
					stresses_reached += 1
					reached_nucleus = True
				else:
					# A consonant before the nucleus.
					final_encoding += '>' # Point towards future nucleus.
			else: 
				# We've reached the nucleus already. Point the other way.
				final_encoding += '<'
		print('{} encoded to {} from boundary indices {} and phonemes {}.'.format( \
			self.letters, final_encoding, self.boundary_buffer, self.phonemes))

		self.syllable_boundary_encodings = final_encoding
		return True
	# Dataset a had the stresses per syllable.
	# Dataset b has the encoding patterns.
	# Combine them here.
	# Return true when encoding successful, else false.
	def inject_stresses(self, encoding_pattern):
		slots = encoding_pattern.count('_')
		# Quick fix for 'ed' and 'es' words lacking syllables.
		if (self.syllable_count == slots + 1) \
		and encoding_pattern.endswith('<<<') and (self.letters[-2] == 'e'):
			# Adds a stress location for the second to last character.
			s = encoding_pattern
			encoding_pattern = s[:-2] + '_' + s[-1:]
			slots += 1

		if slots != self.syllable_count:
			# TODO: Figure out what to do with "ism" words.
			#print('{}, {}, {} had {} slots but {} syllables'.format(self.letters, \
			#	self.phonemes, encoding_pattern, slots, self.syllable_count))
			return False
		final_encoding = ''
		index = 0
		for ch in encoding_pattern:
			if(ch == '_'):
				final_encoding += self.stresses[index] # Adds the stress associated with that syllable
				index += 1
			else:
				final_encoding += ch # Adds > or <
		self.syllable_boundary_encodings = final_encoding
		return True

# Returns a list of word objects loaded from dataset a.
def load_phonemes(a_path):
	corpus = []
	# Dataset a has pronunciation information.
	with open(a_path, 'r', encoding='latin-1') as a:
		ending_in_schwa_count = 0
		for line in a:
			# Ignore comments
			if line.startswith(';;;'): 
				continue

			line = line.lower().strip()
			word, pronunciation = line.split('  ')
			pronunciation = pronunciation.lstrip() # Sometimes, the separator was three spaces instead of two.

			# Let's not skip homonyms so soon. We might be able to salvage some pronunciations with the duplicates.
			#if '(' in word: 
			#	continue	# Skip homonyms.

			letters = ''
			phonemes = ''
			stresses = []
			# Load letters.
			for ch in word:
				letters += ch if ch in alphabet else ''
			# Load pronunciations.
			current = ''
			for ch in pronunciation:
				if ch == ' ':		# The current phoneme just ended.
					# Edge case: account for schwa, which is only implicitly defined in dataset a.
					if current == 'ah' and stresses[-1] == '0':
						phonemes += 'x'
						current = ''
						continue
					# Regular case. Map to S&R representation and add to phonemes.
					phonemes += phoneme_map[current]
					current = ''
				elif ch in ('0', '1', '2'):	# The current phoneme is about to end. Add the stress.
					stresses += ch
				else:
					current += ch	# Phoneme currently being built.
			# Add last phoneme.
			if current == 'ah' and stresses[-1] == '0':
				ending_in_schwa_count += 1
				phonemes += 'x'
				#print('Word {} that ended in schwa has been fixed to {}'.format(word, phonemes))
				current = ''
			else:
				phonemes += phoneme_map[current]

			# Handle unmapped phonemes.
			# A bit on the theory: these extra phonemes help ascertain
			# 1:1 mapping between letters and phonemes, preventing "null letters."
			for key in unmapped.keys():
				if key in phonemes:
					old = phonemes
					phonemes = phonemes.replace(key, unmapped[key])
					#print('Simplifying {} to {}'.format(old, phonemes))
			corpus.append(Word(letters, phonemes, stresses))
			#print('Added {}, {}, and {} to corpus.'.format(letters, phonemes, stresses))
		print('{} words ending in schwa have been fixed.'.format(ending_in_schwa_count))
	print('{} words added from a.'.format(len(corpus)))
	return corpus

# Returns a dict of words' spellings mapped to syllable boundary encodings, loaded from dataset b.
def load_syllable_encodings(b_path):
	dataset_b = {}
	# Dataset b has syllable boundary information.
	# For the sake of consistency, and simplicity, let's try
	# treating these simple rules for nucleus determination as ground truth.
	with open(b_path, 'r', encoding='latin-1') as b:
		for line in b:
			line = line.lower()
			# Certain lines consist of multiple words.
			line = line.split(' ')
			for word in line:
				letters = ''
				syllable_boundary_encodings = ''
				word.strip() # Remove any extra spaces.
				reached_nucleus = False
				for index, ch in enumerate(word):
					if ch == '-':
						reached_nucleus = False # New syllable. Reset nucleus flag.
						continue
					if ch not in alphabet:
						# Just skip words containing non-alphanumeric chars.
						continue

					letters += ch
					# Every character in a syllable points to the first vowel.

					# Handle aeiou.
					if not reached_nucleus:
						# Handle common vowels.
						if ch in 'aeiou':
							# This is the nucleus. Insert char to be replaced with stress level.
							syllable_boundary_encodings += '_' 
							reached_nucleus = True
						# Handle y, which is a vowel when exclusively bordered by nonvowels.
						elif ch == 'y':
							# The "not reached_nucleus" condition above guarantees left border validity.
							# Right border is valid when at the end of the word,
							# OR when the next letter is nonvowel.
							if (index == len(word) - 1) or \
								(index < len(word) - 1 and (not (word[index + 1] in 'aeiou'))):
								syllable_boundary_encodings += '_' 
								reached_nucleus = True
								continue
							syllable_boundary_encodings += '>' # This y is now proven to be a consonant.
						else:
							# A consonant before the nucleus.
							syllable_boundary_encodings += '>' # Point towards future nucleus.
					else: 
						# We've reached the nucleus already. Point the other way.
						syllable_boundary_encodings += '<'

				#print('{} encoded to {}.'.format(letters, syllable_boundary_encodings))
				# Sanity check: These should always be equal.
				if(len(letters) != len(syllable_boundary_encodings)):
					print('{} does not map evenly on to {}'.format(letters, syllable_boundary_encodings))

				dataset_b[letters] = syllable_boundary_encodings
	print('{} words added from b.'.format(len(dataset_b.keys())))
	return dataset_b

def merge(corpus, dataset_b):
	# Combine the datasets.
	final = []
	# A set of all added spellings. Used to detect duplicates.
	final_spellings = set()
	keys = dataset_b.keys()
	mismatched = 0	# The word was found in b, but the number of syllables differed between a and b.
	unmatched = 0 # The word was not found in b.
	unmatcheds = [] # To attempt to salvage.
	duplicates = 0 # Count words that were duplicated by disabling "Skip homonyms" above.
	# More specifically, we give a's duplicates a chance to merge with b, without 
	# erroneously adding them twice if both fit.

	for word in corpus:
		# We already have this word.
		if word.letters in final_spellings:
			duplicates += 1
			continue

		if word.letters in keys:
			if(word.inject_stresses(dataset_b[word.letters])):
				final.append(word)
				final_spellings.add(word.letters)
			else:
				mismatched += 1
		else:
			unmatched += 1
			unmatcheds.append(word)

			#print('Found {} in dataset b'.format(word.letters))

	print('{} merged, {} mismatched, {} discarded duplicates, {} unmatched.'.format(len(final), mismatched, duplicates, unmatched)) 
	# Attempt to salvage.
	salvaged = 0
	salvageds = []
	# Naively attempt to salvage unmatched words.
	# Common words like "underlings", "underlined", "developed" are not matching.
	# The different endings are to blame.
	# Let's transplant those endings onto hypothetical valid entries that don't include them.
	fixes = \
	[
		['ed', '<<'],
		['s', '<'],
		['d', '<'],
		['ing', '_<<'],
		['ers', '_<<'],
		['er', '_<'],
		['ability', '_>_<_>_'],
		['ly', '>_'],
	]
	fix_counter = {}
	for word in unmatcheds:
		letters = word.letters
		for fix in fixes:
			part = fix[0]
			addendum = fix[1]
			if not letters.endswith(part):
				continue # Skip because doesn't match.

			truncated = letters[:- len(part)] # Remove matching part.

			if (word.letters in final_spellings) or (truncated not in keys):
				continue # Skip because duplicate, or because removal didn't help.

			# Skip because when truncated ends in vowel, addendum's encoding is wrong.
			if (truncated[-1] in 'aeiouy') and (part.startswith('er')):
				continue

			# Valid fix found. 
			# Inject the stresses with the augmented pattern
			if(word.inject_stresses(dataset_b[truncated] + addendum)):
				final.append(word)
				# Prevent duplicate unmatched homonyms from getting entered twice.
				final_spellings.add(word.letters)
				salvaged += 1
				# Iterate the counter.
				fix_counter[part] = fix_counter.get(part, 0) + 1
				#print('Salvaged {} with modified encoding {}'.format(word.letters, word.syllable_boundary_encodings))
			# TODO: Replacements...
	print(fix_counter)
	print('Of the {} unmatched, {} were salvaged.'.format(unmatched, salvaged))
	return final


def populate_word_anchors(final):
	# Populate word anchors.
	# Phoneme nuclei "belong" where the syllable encoding nucleus is.
	# We pair the nuclei's indices to the letter associated with the nucleus.
	for word in final:
		# Count phonemes' nuclei.
		phoneme_nucleus_locations = []
		for i, ch in enumerate(word.phonemes):
			if ch in nuclei:
				phoneme_nucleus_locations.append(i)
		# Count boundary encodings' nuclei.
		encoded_nucleus_locations = []
		for j, ch in enumerate(word.syllable_boundary_encodings):
			if ch in '012':
				encoded_nucleus_locations.append(j)
		# If the lengths are different, a 1:1 mapping cannot be relied upon.
		if len(phoneme_nucleus_locations) != len(encoded_nucleus_locations):
			print('Phonemes disagree with encodings in word {}'.format(word.letters))
			continue
		# If syllable boundary encodings don't map onto letters 1:1, then the implied location is bunk.
		elif len(word.syllable_boundary_encodings) != len(word.letters):
			print('Length of word {} is {} versus encoding ({}) length {}. Index mappings won\'t work.'.format( \
				word.letters, len(word.letters), word.syllable_boundary_encodings, len(word.syllable_boundary_encodings)))
			continue
		for index in range(len(encoded_nucleus_locations)):
			word.anchors.append((encoded_nucleus_locations[index],phoneme_nucleus_locations[index]))
			#print('{}th index in the word {} anchored to the {}th phoneme of {}.'.format( \
			#	encoded_nucleus_locations[index], word.letters, phoneme_nucleus_locations[index], word.phonemes))
	return final

# Dataset a contains only phoneme information.
# Dataset b contains syllable information.
def combine_a_and_b():
	# location of dataset a and b
	a_path = 'Raw/a.txt'
	b_path = 'Raw/b.txt'

	corpus = load_phonemes(a_path)
	dataset_b = load_syllable_encodings(b_path)
	final = merge(corpus, dataset_b)
	final = populate_word_anchors(final)

	# See "Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm"
	from align import Aligner
	aligner = Aligner()
	# This modifies words in the final wordlist in-place. 
	aligner.align(final)
	# Finally, print the dataset.
	out = []
	errors = []
	count = 0
	total = 0

	for word in final:
		# Words with valid 1:1 mappings:
		if(len(word.syllable_boundary_encodings) == len(word.letters) == len(word.phonemes)): 
			out = word.append_self(out)
			count += 1
		# Words without valid 1:1 mappings:
		else:
			errors = word.append_self(errors)
		total += 1
	with open('Out/output.txt', 'w') as c:
		c.writelines(out)

# Dataset c is a version of dataset a that has syllable information (d'oh!).
# Include a path to the aligned output of preprocess_c to skip the alignment step if applicable.
def preprocess_c(aligned_path=None):
	from datetime import datetime
	now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
	corpus = []
	with open('Raw/c.txt') as c:
		imbalanced_count = 0 # These words have too many phonemes, preventing 1-to-1 alignment. Must be pruned.
		ending_in_schwa_count = 0
		all_spellings = set() # Detect duplicates to skip.
		for line in c:
			if line.startswith(';;;'):
				continue
			line = line.lower().strip()
			word, pronunciation = line.split('  ')
			pronunciation = pronunciation.lstrip() # Sometimes, the separator was three spaces instead of two.

			letters = ''
			phonemes = ''
			stresses = []
			unaligned_boundary_buffer = [] 	# Indices of phonemes immediately after a syllable boundary.
											# In other words, the VERY FIRST PHONEME of every syllable after the first. 
											# (will be used to form syllable encodings post-alignment.)
			# Load letters.
			for ch in word:
				# Skip words with punctuation. (Classic example is "A's," where changing to "As" changes its pronunciation.)
				if ch not in alphabet:
					continue
				# Load word's letters.
				letters += ch
			# Skip duplicates.
			if letters in all_spellings:
				continue
			all_spellings.add(letters)
			# Load pronunciations.
			current = ''
			for ch in pronunciation:
				if ch == '-':
					# A dash means the VERY NEXT phoneme will be the start of a new syllable.
					# What's more, we know exactly which index this prophesied phoneme will occupy:
					unaligned_boundary_buffer.append(len(phonemes))
				elif ch in ('0', '1', '2'):	# The current phoneme is about to end. Add the stress.
					stresses += ch
				elif ch == ' ' and current != '':		# The current phoneme just ended.
					# Edge case: account for schwa, which is only implicitly defined in dataset c.
					if current == 'ah' and stresses[-1] == '0':
						phonemes += 'x'
						current = ''
						continue
					# Regular case. Map to S&R representation and add to phonemes.
					phonemes += phoneme_map[current]
					current = ''
				# Prevent spaces surrounding the syllable boundary characters from ruining the "current" buffer.
				elif ch == ' ':
					pass
				else:
					current += ch	# Phoneme currently being built.
			# Add last phoneme.
			if current == 'ah' and stresses[-1] == '0':
				ending_in_schwa_count += 1
				phonemes += 'x'
				#print('Word {} that ended in schwa has been fixed to {}'.format(word, phonemes))
				current = ''
			else:
				phonemes += phoneme_map[current]

			# Handle unmapped phonemes.
			# A bit on the theory: these extra phonemes help ascertain
			# 1:1 mapping between letters and phonemes, preventing "null letters."
			for key in unmapped.keys():
				if key in phonemes:
					old = phonemes
					phonemes = phonemes.replace(key, unmapped[key])
					#if key == 'Izxm':
					#	print('Simplifying {} to {}'.format(old, phonemes))
			# Ignore single-letter words.
			if len(letters) == 1:
				continue
			# Ignore words who have fewer letters than phonemes.
			if len(letters) < len(phonemes):
				#print('Skipped {} {} because it has fewer letters than phonemes.'.format(letters, phonemes))
				imbalanced_count += 1
				continue
			corpus.append(Word(letters, phonemes, stresses, unaligned_boundary_buffer))
			#print('Phonemes {} have syllable boundaries after indices {}'.format(phonemes, corpus[-1].unaligned_boundary_buffer))
			#print('Added {}, {}, and {} to corpus.'.format(letters, phonemes, stresses))
		print('{} words had more phonemes than letters'.format(imbalanced_count))
		print('{} words ending in schwa have been fixed.'.format(ending_in_schwa_count))
	print('{} words added from c.'.format(len(corpus)))

	if aligned_path == None:
		out = []
		# Align.
		# See "Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm"
		from align import Aligner
		aligner = Aligner()
		# This modifies words in the final wordlist in-place. 
		aligner.align(corpus)
		# Save aligned data to skip this step in the future.
		for word in corpus:
			out = word.append_self(out, include_encodings=False) # Encodings haven't been decided upon yet.

		outpath = 'Out/c_aligned_{}.txt'.format(now)
		with open(outpath, 'w', encoding='latin-1') as c:
			c.writelines(out)
			print('Saved file to {}'.format(outpath))
	else:
		loaded_alignment_dict = {}
		with open(aligned_path, 'r', encoding='latin-1') as f:
			# TODO: load aligned phonemes to dict to populate corpus.
			for line in f:
				letters, phonemes = line.split()
				loaded_alignment_dict[letters] = phonemes
		# For each word, update its alignment.
		for word in corpus:
			#print('{}, {}, {}, {}'.format(word.letters, word.phonemes, word.letters, loaded_alignment_dict[word.letters]))
			word.phonemes = loaded_alignment_dict[word.letters]

	# Now we need to readjust each words' indices of word boundaries.
	final = []
	for word in corpus:
		successful_adjustment = word.adjust_boundary_indices()
		successful_encoding = word.encode_boundaries_post_alignment()
		if successful_adjustment and successful_encoding:
			final.append(word)


	out = []
	for word in final:
		out = word.append_self(out)
	with open('Out/output_c_{}.txt'.format(now), 'w') as c:
		c.writelines(out)
	return final



#combine_a_and_b()
corpus = preprocess_c('Out/c_aligned_2023-11-11-08-17-52.txt')














