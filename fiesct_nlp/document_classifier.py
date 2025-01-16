from spacy import Language
from medspacy.postprocess import postprocessing_functions

SCREEN_POSITIVE_PATTERN = r"((Sometimes|often) true|yes)"
SCREEN_NEGATIVE_PATTERN = r"(no|never)"

@Language.factory("fiesct_document_classifier")
class DocumentClassifier:
    """
    """
    name = "fiesct_document_classifier"


    _SCREENER_CLASS = "FOOD_INSECURITY_SCREEN"
    _FOOD_INSECURITY_CLASS = "FOOD_INSECURITY"
    _FOOD_SECURITY_CLASS = "FOOD_SECURITY"
    _LONG_TERM_FOOD_ASSISTANCE_CLASS = "LONG_TERM_FOOD_ASSISTANCE"
    _FOOD_ASSISTANCE_CLASS = "FOOD_ASSISTANCE"
    _TARGET_CLASSES = {_FOOD_INSECURITY_CLASS, _FOOD_ASSISTANCE_CLASS,
                       _LONG_TERM_FOOD_ASSISTANCE_CLASS, _SCREENER_CLASS,
                       _FOOD_SECURITY_CLASS, "ACCESS"}

    def __init__(self, nlp, name="fiesct_document_classifier", debug=False):
        self.debug = debug
        pass

    def __call__(self, doc, **kwargs):
        doc._.document_classification = self.classify_document(doc, **kwargs)
        return doc

    def classify_document(self, doc, **kwargs):
        classification = self._classify_document(doc, **kwargs)
        return classification

    def _classify_document(self, doc, **kwargs):

        food_insecurity = "unknown"
        food_assistance = "unknown"
        from collections import defaultdict
        asserted_ents = defaultdict(list)
        negated_ents = defaultdict(list)
        seeking_ents = defaultdict(list)
        needs_ents = defaultdict(list)

        for ent in doc.ents:
            if ent._.is_ignored:
                continue
            if ent.label_.upper() == self._SCREENER_CLASS:
                screen_rslt = self.parse_screener(ent)
                if screen_rslt == "positive":
                    food_insecurity = "positive"
                    asserted_ents[ent.label_.upper()].append(ent)
                    if self.debug:
                        print("Positive food insecurity screener")
                elif screen_rslt == "negative":
                    # food_insecurity = "negative" # For now, don't automatically set a negative screener to be negative
                    negated_ents[ent.label_.upper()].append(ent)
                    if self.debug:
                        print("Negative food insecurity screener")
                elif screen_rslt is None:
                    # In this case, we didn't find templated text to classify
                    # but it could say something like 'positive food insecurity screen'
                    if ent._.is_asserted and postprocessing_functions.is_modified_by_category(ent, "POSITIVE"):
                        asserted_ents[ent.label_.upper()].append(ent)
            elif ent.label_.upper() in self._TARGET_CLASSES and ent._.is_asserted:
                if self.debug:
                    print("Found asserted entity:", ent)
                asserted_ents[ent.label_.upper()].append(ent)
            elif ent._.is_hypothetical:
                continue
            else:
                if ent.label_ in self._TARGET_CLASSES and ent._.is_negated:
                    if self.debug:
                        print("Found negated entity:", ent)
                    negated_ents[ent.label_.upper()].append(ent)
                if ent._.is_seeking and not ent._.is_negated:
                    seeking_ents[ent.label_.upper()].append(ent)
            if ent._.is_need:
                needs_ents[ent.label_.upper()].append(ent)
        if self.debug:
            print("Asserted entities:", asserted_ents)
            print("Negated entities:", negated_ents)
            print("Seeking ents:", seeking_ents)
            print("Need ents:", needs_ents)

        # If food insecurity wasn't updated during parsing, check the entities
        if food_insecurity == "unknown":
            # Check asserted entities. If there is an asserted food insecurity or screener,
            # then call it food insecurity positive
            if set(asserted_ents.keys()).intersection({self._FOOD_INSECURITY_CLASS,
                                                       # self._SCREENER_CLASS,
                                                       # self._LONG_TERM_FOOD_ASSISTANCE_CLASS,
                                                       # self._FOOD_ASSISTANCE_CLASS
                                                       }):
                food_insecurity = "positive"
            # Next check for food security, which will be *negative* food security
            elif self._FOOD_SECURITY_CLASS in asserted_ents:
                food_insecurity = "negative"
            elif self._FOOD_INSECURITY_CLASS in negated_ents:
                food_insecurity = "negative"
            elif self._FOOD_ASSISTANCE_CLASS in asserted_ents:
                food_insecurity = "positive"
            elif {"ACCESS", self._FOOD_SECURITY_CLASS}.intersection(negated_ents.keys()):
                food_insecurity = "positive"
            elif "ACCESS" in asserted_ents:
                food_insecurity = "negative"
            elif {self._SCREENER_CLASS}.intersection(negated_ents.keys()):
                food_insecurity = "negative"
            elif set(seeking_ents.keys()).intersection({self._LONG_TERM_FOOD_ASSISTANCE_CLASS, self._FOOD_ASSISTANCE_CLASS}):
                food_insecurity = "positive"
            elif set(needs_ents.keys()).intersection({
                # "FOOD",
                 self._LONG_TERM_FOOD_ASSISTANCE_CLASS, self._FOOD_ASSISTANCE_CLASS}):
                food_insecurity = "positive"


        if food_assistance == "unknown":
            if self._LONG_TERM_FOOD_ASSISTANCE_CLASS in asserted_ents:
                food_assistance = "positive"
            elif self._LONG_TERM_FOOD_ASSISTANCE_CLASS in negated_ents:
                food_assistance = "negative"
            elif self._LONG_TERM_FOOD_ASSISTANCE_CLASS in seeking_ents:
                food_assistance = "seeking"
        classifications = {"food_insecurity": food_insecurity, "food_assistance": food_assistance}
        if self.debug:
            print("Final classifications:", classifications)
        return classifications

    def parse_screener(self, ent):
        final_token = ent[-1]
        window = final_token._.window(n=4, left=False)
        if window._.contains(r"((Sometimes|often) true|yes)", regex=True):
            return "positive"
        if window._.contains(r"(no|never)", regex=True):
            return "negative"
        return
        # if ent._.literal == "Food insecurity screen (v1)":
        #     # Get the next line of the document
        #     final_token = ent[-1]
        #     window = final_token._.window(n=4, left=False)
        #     if window._.contains(r"((Sometimes|often) true|yes)", regex=True):
        #         return "positive"
        #     if window._.contains(r"(no|never)", regex=True):
        #         return "negative"
        # elif ent._.literal == "Food insecurity screen (v2)":
        #     final_token = ent[-1]
        #     window = final_token._.window(n=2, left=False)
        #     if window._.contains(r"\bno\b", regex=True):
        #         return "negative"
        #     elif window._.contains(r"\byes\b", regex=True):
        #         return "positive"




