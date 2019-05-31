# LDA Modeling Functions

import numpy as np
import pandas as pd
from gensim import corpora, models, similarities
import pyLDAvis
import pyLDAvis.gensim
from gensim.models import Phrases
from gensim.models.phrases import Phraser
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel
from six import iteritems
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from operator import itemgetter


def display_topics(model, feature_names, no_top_words):
    '''
    Nick's function to return the top n topics by term frequency
    '''
    
    for topic_idx, topic in enumerate(model.components_):
        print("TOPIC %d:" % (topic_idx))
        print(" ".join([feature_names[i]
                        for i in topic.argsort()[:-no_top_words - 1:-1]]))
        

def train_ldamod(corp=None, raw_text=None, id2word=None, n_topics=10):
    '''
    Helper function to train an LDA model with a set number of topics, and return perplexity
    and coherence of topic model. Main use is iterating through topic counts evaluating proper
    number of topics to use.
    '''
    
    model = models.LdaModel(corp, id2word=id2word, num_topics=n_topics, random_state=50, passes=5, alpha='auto')
    
    # Note this perplexity should be calculated on a holdout set. 
    perp = model.log_perplexity(corp)
    
    coherence_model_lda = CoherenceModel(model=model, texts=raw_text, dictionary=id2word, coherence='c_v')
    coherence_lda = coherence_model_lda.get_coherence()
    
    return (model, perp, coherence_lda)


def apply_topics(model=None, corpus=None, dataframe=None, col_prefix=None):
    '''
    Helper function to merge topic models onto pandas dataframe of original transcripts. 
    Function will return columns associated with probability of each topic per row, 
    as well as the dominant topic. 
    '''
    
    topic_preds = [model[x] for x in corpus]
    best_guess_topic = [max(x, key=itemgetter(1))[0] + 1 for x in topic_preds]
    
    note_topics = pd.DataFrame([dict(x) for x in topic_preds], index=dataframe.index)
    note_topics.columns = [col_prefix + '_topic_' + str(x + 1) for x in note_topics.columns]
    note_topics[col_prefix + '_dominant_topic'] = best_guess_topic
    
    return dataframe.merge(note_topics, how='inner', left_index=True, right_index=True)


def term_retriever(pyldaprepped, lambda_val=0.6, top_n=10):
    '''
    Helper function to return relevant terms to topic based on pyLDAvis implementation.
    Lambda value can be scaled from 0 (most exclusive terms per topic) to 1 (highest frequency
    terms in topic). Original publication suggests around 0.6-0.7 returns interpretable and useful
    terms, and that value is set as the default. 
    '''
    data = pyldaprepped.topic_info.copy().reset_index()
    data['rel'] = lambda_val*(data['logprob']) + (1-lambda_val)*(data['loglift'])
    data = data.sort_values(by='rel', ascending=False)
    data['rank'] = data.groupby("Category").rel.rank(method='first', ascending=False)
    data = data[data['rank'] <= top_n]
    
    return  data.pivot(index='Category', columns='rank')['Term']


def topic_model_scan(intext=None, dictionary=None, topic_counts=range(1,11), split=False):
    '''
    Function that scans input list of topic numbers for LDA and returns a dictionary of the trained models
    along with perplexity and coherence metrics. 
    
    '''
    import warnings
    warnings.filterwarnings('ignore')
    if split:
        intext_filtered = [x.split(' ') for x in intext if x]
    else:
        intext_filtered = [x for x in intext if x]
    
    corpus = [dictionary.doc2bow(text) for text in intext_filtered]
    
    topic_output = {'input_text': intext, 'model_text': intext_filtered, 'corpus': corpus, 'dictionary': dictionary}
    
    for i in topic_counts:
        lda_mod = train_ldamod(corp=corpus, raw_text=intext_filtered, id2word=dictionary, n_topics=i)
        topic_output[i] = lda_mod[0]
        print('N Topics: ' + str(i) + '\t Perplexity: ' + str(np.round(lda_mod[1],4)) + 
              '\t Coherence: ' + str(np.round(lda_mod[2],4)))
        
    return topic_output


def lda_visgen(model_dict, n_topics, refine=False):
    '''
    Creates pyLDAvis output for topic investigation using output from topic_model_scan() function.
    Refined model can be trained using refine=True, which includes more passes of the LDA algorithm.
    '''
    if refine:
        print('Model refinement requested, training new LDA model with', n_topics, 'topics.')
        lda_mod = models.LdaModel(model_dict['corpus'], 
                                  id2word=model_dict['dictionary'], 
                                  num_topics=n_topics, 
                                  random_state=50, passes=5, alpha='auto') 
    else:
        lda_mod = model_dict[n_topics]
    
    return pyLDAvis.gensim.prepare(lda_mod, model_dict['corpus'], model_dict['dictionary'], sort_topics=False), lda_mod