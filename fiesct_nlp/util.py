import medspacy
import spacy
import os
from pathlib import Path

from medspacy.target_matcher import TargetRule
from medspacy.context import ConTextRule
from medspacy.section_detection import SectionRule
from medspacy.preprocess import PreprocessingRule
from medspacy.io import DocConsumer

from .document_classifier import DocumentClassifier

RESOURCES_FOLDER = os.path.join(Path(__file__).resolve().parents[0], "resources")

CONTEXT_ATTRIBUTES = {
    "NEGATED_EXISTENCE": {"is_negated": True},
    "POSSIBLE_EXISTENCE": {"is_uncertain": True},
    "HISTORICAL": {"is_historical": True},
    "HYPOTHETICAL": {"is_hypothetical": True},
    # "FAMILY": {"is_family": True},
    "NOT_RELEVANT": {"is_ignored": True},
    "INFORMATION": {"is_seeking": True},
    "SEEKING": {"is_seeking": True},
    "NEED": {"is_need": True},
    "NO_ISSUE": {"is_negated": True},
    "ENROLLED": {"is_enrolled": True},
}

SECTION_ATTRIBUTES = {
    "past_medical_history": {"is_historical": True},
    "problem_list": {"is_historical": True},
    # "sexual_and_social_history": {"is_historical": True},
    "family_history": {"is_family": True},
    "patient_instructions": {"is_hypothetical": True},
    "education": {"is_hypothetical": True},
    # "patient_needs": {"is_need": True},
    "intake_form": {"is_ignored": True},
}


DOC_CONSUMER_ATTRS = {
    "doc": ["document_classification"],
    "ents": [
        "text",
        "literal",
        "start_char",
        "end_char",
        "label_",
        "section_category" ,
        "is_negated",
        "is_uncertain",
        "is_historical",
        "is_hypothetical",
        "is_family",
        "is_ignored",
        "snippet"
            ],
    "section": DocConsumer.get_default_attrs()["section"],
    "context": DocConsumer.get_default_attrs()["context"],
}

RULE_CLASSES = {
    "concept_tagger": TargetRule,
    "target_matcher": TargetRule,
    "context": ConTextRule,
    "sectionizer": SectionRule,
    "preprocessor": PreprocessingRule
}


def build_nlp(model=None, cfg_file=None, resources_dir=None,

              doc_consumer=False, doc_consumer_attrs=None, default_rules=True,
              medspacy_components=(
                  "medspacy_pyrush",

                                   "medspacy_target_matcher",
                                   "medspacy_context",
                                   "medspacy_sectionizer",
                                   "medspacy_preprocessor",
                                   "medspacy_postprocessor"
                                   )):
    """Loads an NLP model for a specified domain."""
    if model is None:
        # nlp = medspacy.load("en_core_web_sm", enable=('tagger', 'parser') + medspacy_components)
        # for pipe in ('attribute_ruler', 'ner', 'lemmatizer'):
        #     nlp.remove_pipe(pipe)
        nlp = spacy.blank("en")
    elif model == "":
        nlp = spacy.load(model, disable=["tok2vec", "ner"])
    else:
        nlp = spacy.load(model)
    if "medspacy_preprocessor" in medspacy_components:
        from medspacy.preprocess import Preprocessor
        from .resources.preprocess_rules import preprocess_rules
        preprocessor = Preprocessor(nlp.tokenizer)
        preprocessor.add(preprocess_rules)
        nlp.tokenizer = preprocessor
    if "medspacy_pyrush" in medspacy_components:
        nlp.add_pipe("medspacy_pyrush", first=True)
    if "medspacy_concept_tagger" in medspacy_components:
        nlp.add_pipe("medspacy_concept_tagger")
    if "medspacy_target_matcher" in medspacy_components:
        nlp.add_pipe("medspacy_target_matcher")
    if "medspacy_context" in medspacy_components:
        nlp.add_pipe("medspacy_context", config={"span_attrs": CONTEXT_ATTRIBUTES, "rules": None})
    if "medspacy_sectionizer" in medspacy_components:
        nlp.add_pipe("medspacy_sectionizer", config={"span_attrs": SECTION_ATTRIBUTES, "rules": None})
    if "medspacy_postprocessor" in medspacy_components:
        postprocessor = nlp.add_pipe("medspacy_postprocessor")
        from .resources.postprocess_rules import postprocess_rules
        postprocessor.add(postprocess_rules)


    # for name in medspacy_components:
    #     if name not in nlp.pipe_names:
    #         nlp.add_pipe(name)

    nlp = add_rules_from_cfg(nlp, cfg_file, resources_dir)

    if doc_consumer:
        if doc_consumer_attrs is None:
            doc_consumer_attrs = DOC_CONSUMER_ATTRS
        consumer_config = {'dtypes': tuple(doc_consumer_attrs.keys()), 'dtype_attrs': doc_consumer_attrs}
        nlp.add_pipe("medspacy_doc_consumer", config = consumer_config)
    if "medspacy_context" in nlp.pipe_names:
        # Don't allow overlapping entities and modifiers
        nlp.get_pipe("medspacy_context").prune_on_target_overlap = True


    return nlp


def add_rules_from_cfg(nlp, cfg_file=None, resources_dir=None):
    rules = load_rules_from_cfg(cfg_file, resources_dir)
    for (name, component_rules) in rules.items():
        try:
            # NOTE: This is a bit strange, but it prevents changing lots of references in code
            # to prefix with "medspacy_" when it is only needed here.
            pipe_name = name
            if name in ['concept_tagger', 'context', 'target_matcher', 'sectionizer', 'postprocessor']:
                pipe_name = 'medspacy_' + name
                if pipe_name not in nlp.pipe_names:
                    component = nlp.add_pipe(pipe_name)
                else:
                    component = nlp.get_pipe(pipe_name)
        except KeyError:
            raise ValueError("Invalid component:", name)
        component.add(component_rules)

    # Add document classifier
    nlp.add_pipe("fiesct_document_classifier")

    return nlp

def load_rules_from_cfg(cfg_file=None, resources_dir=None):
    if cfg_file is None:
        cfg_file = os.path.join(RESOURCES_FOLDER, "configs", "config.json")
    if not os.path.exists(cfg_file):
        cfg_file2 = os.path.join(RESOURCES_FOLDER, "configs", cfg_file)
        if os.path.exists(cfg_file2):
            cfg_file = cfg_file2
        else:
            raise FileNotFoundError(f"Invalid config filename or filepath: '{cfg_file}'")
    cfg = load_cfg_file(cfg_file)

    if resources_dir is None:
        resources_dir = RESOURCES_FOLDER
    rules = _load_cfg_rules(cfg, resources_dir)
    return rules

def load_cfg_file(filepath):
    import json
    with open(filepath) as f:
        cfg = json.loads(f.read())

    return cfg

def _load_cfg_rules(cfg, resources_dir):
    rules = dict()
    for component, filepaths in cfg["resources"][0].items():
        if component not in RULE_CLASSES:
            raise ValueError(f"Invalid component name {component} in config. "
                             f"Please add custom logic to add these rules to your pipeline. "
                             f"Valid options are: {RULE_CLASSES.keys()}")
        rule_cls = RULE_CLASSES[component]
        rules[component] = []
        for filepath in filepaths:
            abspath = os.path.abspath(os.path.join(resources_dir, filepath))

            rules[component].extend(rule_cls.from_json(abspath))
    return rules

def add_preprocess_rules(nlp):
    pass

def load_cfg_file(filepath):
    import json
    with open(filepath) as f:
        cfg = json.loads(f.read())
    return cfg