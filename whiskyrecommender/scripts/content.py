from typing import List, Any

from gensim.models import LsiModel
from gensim.corpora import Dictionary
from gensim import similarities

class ContentQuery():
    def __init__(self, corpus=None, similarity=None, dictionary=None, embedding_model=None, keyed_content=None):
        self.corpus = corpus
        self.similarity = similarity
        self.dictionary = dictionary
        self.embedding_model = embedding_model
        self.keyed_content = keyed_content


    def generate_similarity(self):
        '''
        generate similarity
        '''
        if self.similarity == None:
            self.similarity = similarities.MatrixSimilarity \
                (self.embedding_model[[self.dictionary.doc2bow(x) for x in self.corpus]])


    def get_topn_matches(self, query=None, topn=5):
        '''
        query similarity object
        '''

        query_emb = self.text_to_emb(query)

        sims = self.similarity[query_emb]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        for i, s in enumerate(sims[0:topn]):
            idx = s[0]
            # Right now we are just using the keyed content as a pd.DataFrame - switch to
            # print(s[0], s[1], ' '.join(self.keyed_content.loc[idx]))
            print(s[0], s[1], self.keyed_content.loc[idx])

    def text_to_emb(self, query=None):
        '''
        convert query text to bow, then embedding
        '''

        query = query.split(' ')
        query_bow = self.dictionary.doc2bow(query)
        query_emb = self.embedding_model[query_bow]

        return query_emb


def retrieve_content(client=None, collection=None):
    '''
    Function to retrieve whisky content from Mongo Collection
    '''


    whisky_content = client[collection]
    # Need to build this out still to put names in with parsed lemmas
    documents = [x for x in whisky_content.find()]
    return documents


if __name__=='__main__':
    profile_lsi_model = LsiModel.load('../models/lemma_lsi100_profile.genmod')
    profile_term_dict = Dictionary.load('../models/tastingnotes_dictionary.gendict')

    query_obj = ContentQuery(dictionary=profile_term_dict, embedding_model=profile_lsi_model)

    print('Everything Worked')