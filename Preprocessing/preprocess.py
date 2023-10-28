# coding: latin-1

# We map phoneme representations defined in dataset a to the ones outlined by Sejnowski and Rosenberg 
# in their 1987 paper "Parallel Networks that Learn to Pronounce English Text."


phoneme_map = \
{
				# FROM		TO 
				# (Example words given in dataset a and S&R's NETTalk paper respectively)
	# VOWELS
	'aa': 'a', 	# _o_dd, 	f_a_ther
	'ay': 'A',	# h_i_de,	b_i_te    *I take HUGE issue with this, but Webster's Dictionary 
	'ao': 'c', 	# _ou_ght,	b_ou_ght   and Google both corroborate that no symbolic distinction 
	'ae': '@',	# _a_t,		b_a_t      exists between "hide" and "bite," even though the 
	'ah': '^',	# h_u_t,	b_u_t      difference in sound is obvious.
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
	# clusters
	'kS': 'K',	# se_x_ual
	'ks': 'X',	# e_xc_ess
	'gz': '#', 	# e_x_amine
	'w^': '*', 	# _o_ne
	'ts': '!',	# na_z_i
	'kw': 'Q'	# _qu_est
}

'''
# These features described in S&R can be teased out of dataset a given additional context.
context_dependent = \
{
	# TODO: Replace 'END' with the actual character.
	# TODO: Replace the dataset a representations with S&R
									# S&R examples:
	['ah0']: 'x',					# _a_bout
	['ah0', 'l', 'END']: 'L',		# bott_le_
	['m', 'END']: 'M',				# absy_m_
	['n', 'END']: 'N'				# butto_n_
}
'''

# These are vowels as defined by S&R. They'll help us populate the dummy letters.
vowels = \
	[
	'a',
	'A',
	'c',
	'@',
	'^',
	'W',
	'i',
	'I',
	'o',
	'O',
	'E',
	'R',
	'e',
	'U',
	'u'
	]


class Word:
	def append_self(self, arr):
		arr.append('{:20} {:20} {:20}\n'.format(self.letters, self.phonemes, self.syllable_boundary_encodings))
		return arr

	def __init__(self, letters, phonemes, stresses):
		self.letters = letters
		self.phonemes = phonemes
		self.stresses = stresses
		self.syllable_count = len(stresses)
	# Database a had the stresses per syllable.
	# Database b has the encoding patterns.
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

def preprocess():
	# To be filled with references to word objects.
	corpus = []
	dataset_b = {}

	alphabet = 'abcdefghijklmnopqrstuvwxyz'

	# Dataset a has pronunciation information.
	with open('Raw/a.txt', 'r', encoding='latin-1') as a:
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
					# Map to S&R representation and add to phonemes.
					phonemes += phoneme_map[current]
					current = ''
				elif ch in ('0', '1', '2'):	# The current phoneme is about to end. Add the stress.
					stresses += ch
				else:
					current += ch	# Phoneme currently being built.
			# Add last phoneme.
			phonemes += phoneme_map[current]

			# Handle unmapped phonemes.
			for key in unmapped.keys():
				if key in phonemes:
					old = phonemes
					phonemes = phonemes.replace(key, unmapped[key])
					#print('Simplifying {} to {}'.format(old, phonemes))
			corpus.append(Word(letters, phonemes, stresses))
			#print('Added {}, {}, and {} to corpus.'.format(letters, phonemes, stresses))
	print('{} words added from a.'.format(len(corpus)))


	# Dataset b has syllable boundary information.
	with open('Raw/b.txt', 'r', encoding='latin-1') as b:
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

	# Combine the datasets.
	final = []
	# A set of all added spellings. Used to detect duplicates.
	final_spellings = set()
	keys = dataset_b.keys()
	mismatched = 0	# The word was found in b, but it had a different number of syllables.
	unmatched = 0 # The word was not found in b.
	unmatcheds = [] # To attempt to salvage.
	duplicates = 0 # These catch duplicate words from disabling "Skip homonyms" above.
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
				continue

			# Found a match. Now search b for the truncated version of the matching word:
			truncated = letters[:- len(part)]
			if (word.letters not in final_spellings) and (truncated in keys):
				# Fixing "er" and "ers" causes broken pattern when ending letter is vowel.
				if (truncated[-1] in 'aeiouy') and (part.startswith('er')):
					continue

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


	# We need to find a way to inject null symbols:

	# aardvark ardvark 1<<<>2<<
	# aardvark a-rdvark 1<<<>2<<

	# abbott @b^t 1<>0<<
	# abbott @b-^t- 1<>0<<

	# First attempt:
	# While phonemes' length does not equal letters' length 
	# Iterate through the phonemes, comparing each character to its respective letter.
	# There are two cases when a - must be injected:
	# 1. The ith phoneme is a vowel but the ith letter is a consonant.
	# 2. The ith phoneme is a consonant but the ith letter is a vowel.

	# No, because this would convert
	# abbreviate ^briviet 0<>>1>02<<	to
	# abbreviate ^br-iviet- 0<>>1>02<<	but what we really need is
	# abbreviate ^-briviet- 0<>>1>02<<

	# EM ALIGNMENT TIME (see 06-DAMPER.pdf, or, Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm)


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
	print('{} words had valid mappings, {} didn\'t'.format(count, total - count))
	# VALID WORDS:
	with open('Out/output.txt', 'w+') as c:
		c.writelines(out)
	with open('Out/errors.txt', 'w+') as c:
		c.writelines(errors)

preprocess()





















