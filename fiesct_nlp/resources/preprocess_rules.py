from medspacy.preprocess import PreprocessingRule
import re

preprocess_rules = [ \
    # PreprocessingRule(re.compile("([a-z])([\s]{2,})([a-z])")),
    PreprocessingRule("([a-z])([\r\n\s]{2,})([a-z])",
                      repl=lambda match: match.group(1) + " " + match.group(3),
                      desc="Replace carriage returns in the middle of sentences with a single space"),
    # PreprocessingRule(re.compile("\[X \]|\[ X\]"), "[X] ",
    #                   desc="Normalize filled-in check box and insert space after to allow tokenizinng"),
    # PreprocessingRule(re.compile("\[\s+\][\s]+"), "[] ",
    #                   desc="Normalize empty check box and insert space after to allow tokenizinng"),
    # PreprocessingRule(re.compile("\( \([\s]+"), "() ",
    #                   desc="Normalize empty check box and insert space after to allow tokenizinng"),

    PreprocessingRule("([a-zA-Z,]) ?([\n\r]){1,}([a-z])",
                      lambda match: match.group(1) + " " + match.group(3),
                      desc="Eliminate carriage returns in the middle of a sentence."),

    PreprocessingRule("\r\n", "\n", desc="Replace carriage returns with a single new line"),
    # PreprocessingRule(re.compile("([A-Za-z][0-9]{2}\.[0-9]{1,3})(,)"),
    #                   lambda match: match.group(1) + " " + match.group(2),
    #                   desc="Lists of ICD-9/10 codes are thrown off by commas"),
    # PreprocessingRule(re.compile("[^\s]+\.(org|com|gov)", re.IGNORECASE), " ", desc="Remove simple URLs"),
    # PreprocessingRule(re.compile("\""), desc="Remove quotations from text."), # TODO: This may be too destructive
    # PreprocessingRule(re.compile("house hold"), "household"),

]