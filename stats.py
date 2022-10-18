# Copyright (c) 2022, Daniel E. Gaskell and Claire L. Bowern.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software, datasets, and associated documentation files (the "Software
# and Datasets"), to deal in the Software and Datasets without restriction,
# including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software and Datasets, and to
# permit persons to whom the Software is furnished to do so, subject to the
# following conditions:
# 
# - The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software and Datasets.
# - Any publications making use of the Software and Datasets, or any substantial
#   portions thereof, shall cite the Software and Datasets's original publication:
# 
# > Gaskell, Daniel E., Claire L. Bowern, 2022. Gibberish after all? Voynichese
#   is statistically similar to human-produced samples of meaningless text. CEUR
#   Workshop Proceedings, International Conference on the Voynich Manuscript 2022,
#   University of Malta.
#   
# THE SOFTWARE AND DATASETS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
# EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE AND DATASETS.

import os
import string
import argparse
import csv
import math
import statistics
import re
import random
import numpy
import scipy
import distance
import zlib
import unidecode
from scipy import stats
from glob import glob
from collections import defaultdict, deque, Counter
from esda import Moran
from libpysal.weights.util import lat2W

# options and setup
do_levenshtein = 1
ngram_max_len = 3
subset_iterations = 100
subset_words = 200
charbias_cutoff = 20 # character must appear at least this many times to be included in bias averages
csv_out = []

# command-line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument('file', nargs='+')
args = argparser.parse_args()
files = []
for file in args.file:
    files.extend(glob(file))
    
def char_entropy(text):
    # Third-order Markov model of text stream (note: sensitive to text length!)
    # http://pit-claudel.fr/clement/blog/an-experimental-estimation-of-the-entropy-of-english-in-50-lines-of-python-code
    
    # This function is adapted from Clement Pit-Claudel's implementation.
    # Copyright (C) 2013, Clement Pit--Claudel (http://pit-claudel.fr/clement/blog)
    # 
    # Permission is hereby granted, free of charge, to any person obtaining a copy of 
    # this software and associated documentation files (the "Software"), to deal in 
    # the Software without restriction, including without limitation the rights to 
    # use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    # the Software, and to permit persons to whom the Software is furnished to do so, 
    # subject to the following conditions:
    # 
    # The above copyright notice and this permission notice shall be included in all 
    # copies or substantial portions of the Software.
    # 
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    # FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
    # COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
    # IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
    # CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    
    def tokenize(file, tokenizer):
        for line in file:
            for token in tokenizer(line.lower().strip()):
                yield token
                    
    def chars(file):
        return tokenize(file, lambda s: s + " ")
        
    def words(file):
        return tokenize(file, lambda s: re.findall(r"[a-zA-Z']+", s))

    def markov_model(stream, model_order):
        model, stats = defaultdict(Counter), Counter()
        circular_buffer = deque(maxlen = model_order)
        
        for token in stream:
            prefix = tuple(circular_buffer)
            circular_buffer.append(token)
            if len(prefix) == model_order:
                stats[prefix] += 1
                model[prefix][token] += 1
        return model, stats

    def entropy(stats, normalization_factor):
        return -sum(proba / normalization_factor * math.log2(proba / normalization_factor) for proba in stats.values())

    def entropy_rate(model, stats):
        return sum(stats[prefix] * entropy(model[prefix], stats[prefix]) for prefix in stats) / sum(stats.values())

    model, stats = markov_model(chars(text), 2)
    return entropy_rate(model, stats)
    
numbers_allowed = ["Historical - Mayan (Kaqchikel) - Literary - Annals of the Cakchiquels",
                   "Voynichese - v101"]

# iterate through files
for input_file in files:
    # validate/extend command-line arguments
    if input_file[-4:].lower() != '.txt':
        print('Input file(s) must be in .txt format.')
        quit()
    input_stem = os.path.basename(input_file)[:-4] # stem filename w/o extension
    file_class = input_stem[0:input_stem.find(' - ')]

    # read text into list of lines
    print(input_file)
    lines = open(input_file, encoding='utf-8').readlines()

    # clean text
    for i in range(len(lines)):
        lines[i] = lines[i].strip()                                                     # whitespace and line breaks
        if input_stem.find("Enciphered - ") == -1:
            lines[i] = unidecode.unidecode(lines[i])                                    # simplify unicode characters to ASCII
            if file_class != "Voynichese":
                lines[i] = lines[i].lower()                                             # uppercase
                lines[i] = lines[i].translate(str.maketrans("", "", string.punctuation))# punctuation
            if input_stem not in numbers_allowed:
                lines[i] = re.sub("\d+", "", lines[i])                                  # numbers
        if lines[i] == '__________':
            lines[i] = ''                                                               # page markers (not currently used)

    with open(os.path.dirname(input_file) + "\\Cleaned\\" + input_stem + ".txt", "w", encoding='utf-8') as cleaned:
        for line in lines:
            cleaned.write("%s\n" % line)
            
    # metrics definitions
    wordlen_mean = []
    wordlen_std = []
    wordlen_skew = []
    wordlen_unique_mean = []
    wordlen_unique_std = []
    wordlen_unique_skew = []
    wordlen_autocorr = []
    wordunique_mean = []
    wordunique_std = []
    wordunique_skew = []
    wordchange_mean = []
    wordchange_std = []
    wordchange_skew = []
    worddist_max = []
    worddist_shape = []
    chardist_max = []
    wordbias_mean = []
    wordbias_std = []
    wordbias_skew = []
    wordbias_lines_mean = []
    wordbias_lines_std = []
    wordbias_lines_skew = []
    chardist_shape = []
    ngramdist_max = []
    ngramdist_shape = []
    charbias_mean = []
    charbias_std = []
    charbias_skew = []
    charbias_words_mean = []
    charbias_words_std = []
    charbias_words_skew = []
    unique_words = []
    repeated_words = []
    tripled_words = []
    unique_chars = []
    repeated_chars = []
    tripled_chars = []
    unique_ngrams = []
    entropy = []
    compression = []
    zipf = []
    flipped_pairs = []

    # main data-gathering loop
    for i in range(0, subset_iterations):
        # pull random subset of lines with at least subset_words words
        num_words = 0
        lines_sub = []
        while num_words < subset_words:
            for t in range(random.randint(0, len(lines)), len(lines)):
                lines_sub.append(lines[t])
                num_words += len(lines[t].split(' '))
                if num_words >= subset_words:
                    break

        # stats definitions
        docwords = []
        wordbank = {}
        wordlen_bank = []
        wordlen_unique_bank = []
        wordunique_bank = {}
        wordchange_bank = []
        word_heat = {}
        word_variation = {}
        word_heat_lines = {}
        word_lines_variation = {}
        charbank = {}
        ngram_bank = {}
        ngram_bank_unique = {}
        ngram_heat = {}
        ngram_heat_words = {}
        ngram_heat_normalized = {}
        ngram_heat_words_normalized = {}
        ngram_variation = {}
        ngram_variation_words = {}

        # line-by-line stats
        num_chars = 0
        for line_index, line in enumerate(lines_sub):
            # read line into list of words
            words = line.split(' ')
            words = list(filter(None, words)) # remove blank words
            docwords.extend(words)

            # add words to wordbank
            for index, word in enumerate(words):
                if word not in wordbank:
                    wordbank[word] = 0
                    word_heat[word] = [0, 0, 0, 0, 0] # initialize heatmap
                    word_heat_lines[word] = [0, 0, 0, 0, 0] # initialize line heatmap
                wordbank[word] += 1
                word_heat[word][math.floor((index / len(words)) * 5)] += 1
                word_heat_lines[word][math.floor((line_index / len(lines_sub)) * 5)] += 1

                # add length to wordlen_bank
                wordlen_bank.append(len(word))
                num_chars += len(word)
        
        # whole-document stats
        word_repeats = 0
        word_triples = 0
        char_repeats = 0
        char_triples = 0
        word_flips = 0
        last_word = ''
        last_word2 = ''
        for word in docwords:
            if word == last_word:
                # count repeated words
                word_repeats += 1
                
                # count triply repeated words
                if last_word == last_word2:
                    word_triples += 1
            else:
                # length-normalized Levenshtein distance to prior word
                if do_levenshtein == 1:
                    wordchange_bank.append(distance.levenshtein(word, last_word) / len(word))
                else:
                    wordchange_bank.append(1)
                    
            # find reversed pairs
            last_word2 = ''
            for word2 in docwords:
                if word2 == last_word and last_word2 == word:
                    word_flips += 1
                    break
                last_word2 = word2
                
            # letter-by-letter stats, within words
            last_char = ''
            for char in word:
                # count letter frequencies
                if char not in charbank:
                    charbank[char] = 0
                charbank[char] += 1
                
                # count repeated letters
                if char == last_char:
                    char_repeats += 1
                
                # count triply repeated letters
                if char == last_char and last_char == last_char2:
                    char_triples += 1

                last_char2 = last_char
                last_char = char
                
            last_word2 = last_word
            last_word = word
            
        # word-by-word stats
        for word in wordbank:
            word_len = len(word)

            # add length to wordlen_unique_bank
            wordlen_unique_bank.append(word_len)
            
            # calculate word uniqueness (mean length-normalized Levenshtein distance to every word in the bank)
            if do_levenshtein == 1: # allow this to be turned off (slowest metric by far)
                for word2 in wordbank:
                    if (word2 + "_" + word) not in wordunique_bank:
                        wordunique_bank[word + "_" + word2] = (distance.levenshtein(word, word2) / len(word))
                    
            # calculate coefficient of variance for word_heat
            word_heat_mean = statistics.mean(word_heat[word])
            word_variation[word] = statistics.stdev(word_heat[word]) / word_heat_mean
                
            # calculate coefficient of variance for word_heat_lines
            word_heat_lines_mean = statistics.mean(word_heat_lines[word])
            word_lines_variation[word] = statistics.stdev(word_heat_lines[word]) / word_heat_lines_mean
            
            # add ngrams to ngram_bank and ngram_heat_words
            for ngram_index in range(word_len):
                for ngram_len in range(1, ngram_max_len+1):
                    if ngram_index + ngram_len <= word_len:
                        ngram = word[ngram_index: ngram_index + ngram_len]
                        if ngram not in ngram_bank:
                            ngram_bank[ngram] = 0
                            ngram_bank_unique[ngram] = 0
                            ngram_heat[ngram] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # initialize heatmap
                            ngram_heat_words[ngram] = [0, 0, 0, 0, 0] # initialize word heatmap
                        ngram_bank[ngram] += wordbank[word]
                        ngram_bank_unique[ngram] += 1
                        ngram_heat_words[ngram][round((ngram_index / (word_len - (ngram_len - 1))) * 4)] += 1

        # line-by-line stats (second pass)
        for line in lines_sub:
            line_len = len(line)

            # add ngrams to ngram_heat
            for ngram_index in range(line_len):
                for ngram_len in range(1, ngram_max_len+1):
                    if ngram_index + ngram_len <= len(line):
                        ngram = line[ngram_index: ngram_index + ngram_len]
                        if ' ' not in ngram:
                            ngram_heat[ngram][round((ngram_index / (line_len - (ngram_len - 1))) * 9)] += 1

        # ngram-by-ngram stats
        for ngram in ngram_bank:
            ngram_heat_mean = statistics.mean(ngram_heat[ngram])
            ngram_heat_words_mean = statistics.mean(ngram_heat_words[ngram])
            
            #if len(ngram) == 1:
            #   print(ngram)
            #   print(ngram_heat[ngram])
            #   print(statistics.stdev(ngram_heat[ngram]) / ngram_heat_mean)
            
            # calculate coefficient of variance for ngram_heat and ngram_heat_words
            ngram_variation[ngram] = statistics.stdev(ngram_heat[ngram]) / ngram_heat_mean
            ngram_variation_words[ngram] = statistics.stdev(ngram_heat_words[ngram]) / ngram_heat_words_mean
            
            # produce heatmaps normalized to percent of mean
            #ngram_heat_normalized[ngram] = [x / ngram_heat_mean for x in ngram_heat[ngram]]
            #ngram_heat_words_normalized[ngram] = [x / ngram_heat_words_mean for x in ngram_heat_words[ngram]]
            
        # compile metrics for this run
        wordlen_mean.append(statistics.mean(wordlen_bank))
        wordlen_std.append(statistics.stdev(wordlen_bank))
        wordlen_skew.append(stats.skew(wordlen_bank))
        wordlen_unique_mean.append(statistics.mean(wordlen_unique_bank))
        wordlen_unique_std.append(statistics.stdev(wordlen_unique_bank))
        wordlen_unique_skew.append(stats.skew(wordlen_unique_bank))
        wordlen_autocorr.append(Moran(wordlen_bank, lat2W(nrows=len(wordlen_bank), ncols=1)).I)
        
        if do_levenshtein == 1:
            wordunique_bank_list = list(wordunique_bank.values())
            wordunique_mean_value = statistics.mean(wordunique_bank_list)
            wordunique_mean.append(wordunique_mean_value)
            wordunique_std.append(statistics.stdev(wordunique_bank_list))
            wordunique_skew.append(stats.skew(wordunique_bank_list))
            
            wordchange_bank = [(value / wordunique_mean_value) for value in wordchange_bank] # normalize values to mean (so as to less directly track wordunique_mean)
            wordchange_mean.append(statistics.mean(wordchange_bank))
            wordchange_std.append(statistics.stdev(wordchange_bank))
            wordchange_skew.append(stats.skew(wordchange_bank))
        else:
            wordunique_mean.append(1)
            wordunique_std.append(1)
            wordunique_skew.append(1)
            
            wordchange_mean.append(1)
            wordchange_std.append(1)
            wordchange_skew.append(1)
            
        wordbank_sorted = sorted(list(wordbank.values()), reverse=True)
        if (len(wordbank_sorted) > 25):
            wordbank_sorted = wordbank_sorted[0:25] # truncate to top 25 words, to help decouple from unique_words (FIXME not working very well?)
        #wordbank_sorted = [value/len(wordbank) for value in wordbank_sorted] # normalize to number of unique words
        loc, scale = scipy.stats.expon.fit(wordbank_sorted)
        worddist_max.append(wordbank_sorted[0])
        worddist_shape.append(scale)
        
        wordbias_list = [[value]*wordbank[key] for key,value in word_variation.items()] # duplicate items * number of word occurrences (weighted average, to avoid giving too much weight to rare words that will always look more biased)
        wordbias_list = [item for sublist in wordbias_list for item in sublist] # flatten list
        wordbias_mean.append(statistics.mean(wordbias_list))
        wordbias_std.append(statistics.stdev(wordbias_list))
        wordbias_skew.append(stats.skew(wordbias_list))
        
        wordbias_lines_list = [[value]*wordbank[key] for key,value in word_lines_variation.items()] # duplicate items * number of word occurrences (weighted average, to avoid giving too much weight to rare words that will always look more biased)
        wordbias_lines_list = [item for sublist in wordbias_lines_list for item in sublist] # flatten list
        wordbias_lines_mean.append(statistics.mean(wordbias_lines_list))
        wordbias_lines_std.append(statistics.stdev(wordbias_lines_list))
        wordbias_lines_skew.append(stats.skew(wordbias_lines_list))
        
        charbank_sorted = sorted(list(charbank.values()), reverse=True)
        charbank_sorted = [value/num_chars for value in charbank_sorted] # normalize to number of characters, to decouple from word length
        loc, scale = scipy.stats.expon.fit(charbank_sorted)
        chardist_max.append(charbank_sorted[0])
        chardist_shape.append(scale)
        
        ngram_bank_sorted = sorted(list(ngram_bank.values()), reverse=True)
        loc, scale = scipy.stats.expon.fit(ngram_bank_sorted)
        ngramdist_max.append(ngram_bank_sorted[0])
        ngramdist_shape.append(scale)
        
        char_variation = {key:value for key,value in ngram_variation.items() if len(key) == 1}
        char_variation_words = {key:value for key,value in ngram_variation_words.items() if len(key) == 1}
        
        charbias_list = [[value]*ngram_bank[key] for key,value in char_variation.items()] # duplicate items * number of ngram occurrences (weighted average, to avoid giving too much weight to rare ngrams that will always look more biased)
        charbias_list = [item for sublist in charbias_list for item in sublist] # flatten list
        charbias_mean.append(statistics.mean(charbias_list))
        charbias_std.append(statistics.stdev(charbias_list))
        charbias_skew.append(stats.skew(charbias_list))
        
        charbias_words_list = [[value]*ngram_bank[key] for key,value in char_variation_words.items()] # duplicate items * number of ngram occurrences (weighted average, to avoid giving too much weight to rare ngrams that will always look more biased)
        charbias_words_list = [item for sublist in charbias_words_list for item in sublist] # flatten list
        charbias_words_mean.append(statistics.mean(charbias_words_list))
        charbias_words_std.append(statistics.stdev(charbias_words_list))
        charbias_words_skew.append(stats.skew(charbias_words_list))

        unique_words.append(len(wordbank))
        repeated_words.append(word_repeats / num_words)     
        tripled_words.append(word_triples / num_words)     
        unique_chars.append(len(charbank))
        repeated_chars.append(char_repeats / num_chars)
        tripled_chars.append(char_triples / num_chars)
        unique_ngrams.append(len(ngram_bank_unique))
        
        entropy.append(char_entropy(lines_sub))
        
        docwords_string = " ".join(docwords)
        compressed_string = zlib.compress(docwords_string.encode(), 9)
        compression.append(len(compressed_string) / len(docwords_string))

        # Urzua (2000)'s LMZ test statistic for Zipf's law (not doing a t-test here, just comparing the test statistic across samples to see how close they are)
        wordbank_sorted_cut = wordbank_sorted[:int(len(wordbank_sorted) / 2)]
        n = len(wordbank_sorted_cut)
        z1 = 1 - (1/n) * sum([math.log(xi / wordbank_sorted_cut[-1]) for xi in wordbank_sorted_cut])
        z2 = 1/2 - (1/n) * sum([wordbank_sorted_cut[-1] / xi for xi in wordbank_sorted_cut])
        lmz = 4*n * (z1**2 + 6*z1*z2 + 12*z2**2)
        zipf.append(lmz)
        
        flipped_pairs.append(word_flips / num_words)
        
    # compile metrics for this file
    csv_out.append([input_stem,
                    statistics.mean(wordlen_mean),          statistics.mean(wordlen_std),           statistics.mean(wordlen_skew),
                    statistics.mean(wordlen_unique_mean),   statistics.mean(wordlen_unique_std),    statistics.mean(wordlen_unique_skew),
                    statistics.mean(wordlen_autocorr),
                    statistics.mean(wordunique_mean),       statistics.mean(wordunique_std),        statistics.mean(wordunique_skew),
                    statistics.mean(wordchange_mean),       statistics.mean(wordchange_std),        statistics.mean(wordchange_skew),
                    statistics.mean(worddist_max),          statistics.mean(worddist_shape),
                    statistics.mean(wordbias_mean),         statistics.mean(wordbias_std),          statistics.mean(wordbias_skew),
                    statistics.mean(wordbias_lines_mean),   statistics.mean(wordbias_lines_std),    statistics.mean(wordbias_lines_skew),
                    statistics.mean(chardist_max),          statistics.mean(chardist_shape),
                    statistics.mean(ngramdist_max),         statistics.mean(ngramdist_shape),
                    statistics.mean(charbias_mean),         statistics.mean(charbias_std),          statistics.mean(charbias_skew),
                    statistics.mean(charbias_words_mean),   statistics.mean(charbias_words_std),    statistics.mean(charbias_words_skew),
                    statistics.mean(unique_words),          statistics.mean(repeated_words),        statistics.mean(tripled_words),
                    statistics.mean(unique_chars),          statistics.mean(repeated_chars),        statistics.mean(tripled_chars),
                    statistics.mean(unique_ngrams),
                    statistics.mean(entropy),
                    statistics.mean(compression),
                    statistics.mean(zipf),
                    statistics.mean(flipped_pairs)])

# export csv of metrics from all input files
with open('metrics.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['text',
                    'wordlen_mean',                         'wordlen_std',                          'wordlen_skew',
                    'wordlen_unique_mean',                  'wordlen_unique_std',                   'wordlen_unique_skew',
                    'wordlen_autocorr',
                    'wordunique_mean',                      'wordunique_std',                       'wordunique_skew',
                    'wordchange_mean',                      'wordchange_std',                       'wordchange_skew',
                    'worddist_max',                         'worddist_shape',
                    'wordbias_mean',                        'wordbias_std',                         'wordbias_skew',
                    'wordbias_lines_mean',                  'wordbias_lines_std',                   'wordbias_lines_skew',
                    'chardist_max',                         'chardist_shape',
                    'ngramdist_max',                        'ngramdist_shape',
                    'charbias_mean',                        'charbias_std',                         'charbias_skew',
                    'charbias_words_mean',                  'charbias_words_std',                   'charbias_words_skew',
                    'unique_words',                         'repeated_words',                       'tripled_words',
                    'unique_chars',                         'repeated_chars',                       'tripled_chars',
                    'unique_ngrams',
                    'entropy',
                    'compression',
                    'zipf',
                    'flipped_pairs'])
    for csv_line in csv_out:
        writer.writerow(csv_line)
