# Comparing the Voynich Manuscript to human-produced gibberish

This repository contains code and datasets associated with the paper:

> Gaskell, Daniel E., Claire L. Bowern, 2022. Gibberish after all? Voynichese
  is statistically similar to human-produced samples of meaningless text. CEUR
  Workshop Proceedings, International Conference on the Voynich Manuscript 2022,
  University of Malta.
  
## Abstract

The text of the Voynich Manuscript (VMS) has often been regarded as too
non-random to be meaningless. However, if the VMS is indeed a hoax, it was
probably not produced by a purely random process but rather by some form of
automatic writing or glyptolalia in which the scribe(s) simply invented
meaningless text as they went based on an intuitive impression of what written
language ought to look like. Here, we show that such intuitive "gibberish" is
significantly non-random and in fact exhibits many of the same statistical
peculiarities as Voynichese. We recruited 42 volunteers to write short
"gibberish" documents and statistically compared them to several transcriptions
of the VMS and a large corpus of linguistically meaningful texts. We find that
"gibberish" writing varies widely in its statistical properties and, depending
on the sample, is able to replicate either natural language or Voynichese across
nearly all of the metrics which we tested, including traditional criteria for
identifying natural language such as Zipf’s law. However, gibberish tends to
exhibit lower total information content than meaningful text; higher repetition
of words and characters, including triple repeats; greater biases in character
placement within lines and word placement within sections; positive
autocorrelation of word lengths (i.e., a tendency for words to cluster
short-short-long-long rather than short-long-short-long); and a weaker average
fit to Zipf’s law. The majority of these properties are also observed in
Voynichese. A machine-learning model trained to distinguish meaningful text from
gibberish in our dataset identified most VMS transcriptions as more closely
resembling gibberish than meaningful text. We argue that these results refute
the idea that the low-level linguistic structure of the VMS text is too
non-random to be meaningless. However, our writing samples are too short to test
whether the higher-level structure of VMS pages and quires could also be
produced by gibberish.

## Data and extended output

Full gibberish datasets may be found in the "data" folder, with full datasets of
statistical metrics in the "results" folder. See [here](results/plots.md) for an
archive of extended plots for each statistical metric.
  
# License and copyright

Unless otherwise indicated, the source code and gibberish datasets contained in
this repository (but not the Voynichese and meaningful text datasets - see the
associated documentation) are provided under the modified MIT license below.
Because the gibberish datasets were collected from a human experiment, we are
unable to provide full metadata on each participant or scans of their full
documents which might contain identifiable information; however, the anonymized
Unicode transcriptions used in the paper are provided.

---

Copyright (c) 2022, Daniel E. Gaskell and Claire L. Bowern.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software, datasets, and associated documentation files (the "Software
and Datasets"), to deal in the Software and Datasets without restriction,
including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software and Datasets, and to
permit persons to whom the Software is furnished to do so, subject to the
following conditions:

- The above copyright notice and this permission notice shall be included
  in all copies or substantial portions of the Software and Datasets.
- Any publications making use of the Software and Datasets, or any substantial
  portions thereof, shall cite the Software and Datasets's original publication:

> Gaskell, Daniel E., Claire L. Bowern, 2022. Gibberish after all? Voynichese
  is statistically similar to human-produced samples of meaningless text. CEUR
  Workshop Proceedings, International Conference on the Voynich Manuscript 2022,
  University of Malta.
  
THE SOFTWARE AND DATASETS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE AND DATASETS.