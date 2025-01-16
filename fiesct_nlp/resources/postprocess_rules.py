from medspacy.postprocess import PostprocessingRule, PostprocessingPattern, postprocessing_functions



def set_ignored(ent, i, x="ents", y=None,  value=True):
    ent._.is_ignored = value

def set_negated(ent, i, x="ents", y=None, value=True):
    ent._.is_negated = value

postprocess_rules = [
    PostprocessingRule(patterns=[
        PostprocessingPattern(lambda ent: ent.text.lower() == "snap", True),
        PostprocessingPattern(lambda ent: ent._.window(25, left=True, right=True)._.contains(r"(strengths|needs|abilities|preferences)", case_insensitive=True), True),
        # PostprocessingPattern(lambda ent: ent._.window(25, left=False)._.contains("needs"), True),
    ],
    action=set_ignored,
    description="Disambiguate SNAP (food stamps) with 'Strengths, Needs, Action, Plan'"
    ),

    PostprocessingRule(patterns=[
        PostprocessingPattern(lambda ent: True),
        PostprocessingPattern(lambda ent: ent.label_ in ("FOOD_INSECURITY_SCREEN", "FOOD_INSECURITY")),
        PostprocessingPattern(lambda ent: ent._.window(4, left=False)._.contains(r"(due|not perform|completed)"), True),
    ],
        action=set_ignored,
        description="Ignore phrases saying that the food insecurity screener is due or was not performed."),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in ( "FOOD",)),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_text(ent, r"lack", regex=True)),
            PostprocessingPattern(lambda ent: ent._.is_ignored is False),
            PostprocessingPattern(lambda ent: ent.sent._.contains("related") is False),
            PostprocessingPattern(lambda ent: ent.sent._.contains("knowledge") is False),
        ],
        action=postprocessing_functions.set_label,
        label="FOOD_INSECURITY",
        description="Change modifier/target 'lack of' --> 'food' to food insecurity"
    ),
    PostprocessingRule(
            patterns=[
                PostprocessingPattern(lambda ent: ent.label_ in ("FOOD_SECURITY", "ACCESS", "FOOD")),
                PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "NO_ISSUE"))
            ],
            action=postprocessing_functions.set_label,
            label="FOOD_SECURITY",
            description="Change modifier/target 'no issue' --> 'food' to food security"
    ),

    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in ( "ACCESS",)),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "POSITIVE"))
        ],
        action=postprocessing_functions.set_label,
        label="FOOD_SECURITY",
        description="Change modifier/target 'access' --> 'yes' to food security"
    ),
    PostprocessingRule(
            patterns=[
                PostprocessingPattern(lambda ent: ent.label_ == "LONG_TERM_FOOD_ASSISTANCE"),
                PostprocessingPattern(lambda ent: (ent._.is_enrolled + ent._.is_seeking + ent._.is_need) == 0),
            ],
            action=set_ignored,
            description="Require mentions of food assistance to be modified by 'enrolled' or 'seeking'"
        ),
        PostprocessingRule(
                patterns=[
                    PostprocessingPattern(lambda ent: ent.label_ == "FOOD_INSECURITY"),
                    PostprocessingPattern(lambda ent: ent._.section_category == "clinical_reminders"),
                    PostprocessingPattern(lambda ent: ent._.is_negated is False),
                    PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "POSITIVE")
                                                      is False),

                ],
                action=set_ignored,
                description="If 'food insecurity' is mentioned in a section discussing clinical reminders "
                            "and there isn't any evidence of positive or negative results, "
                            "ignore it as just saying that the screening was performed."
            ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ in ("FOOD_ASSISTANCE", "LONG_TERM_FOOD_ASSISTANCE")),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "DENIED")),
        ],
        action=postprocessing_functions.set_label,
        label="FOOD_SECURITY",
        description="Change mentions of 'denies needing food assistance' to food_security"
    ),
    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent._.literal == "<FOOD ORGANIZATION>"),
    #         PostprocessingPattern(lambda ent: ent.sent._.contains(r"\b(food|meal|eat)\b") is False)
    #     ],
    #     action=set_ignored,
    #     description="Disambiguate acronyms like 'VOA' to be specifically referring to food services"
    # ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ == "FOOD"),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "WORRY")),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "AFFORD")),
        ],
        action=postprocessing_functions.set_label,
        label="FOOD_INSECURITY",
        description="Replace 'worried about affording food' with 'food_insecurity'"
    ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ == "FOOD_SECURITY"),
            PostprocessingPattern(lambda ent: ent._.is_negated is False),
            PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "ASSISTANCE")),
        ],
        action=set_negated,
        description="Replace 'assist with food security' with negated 'food security'"
    ),
    PostprocessingRule(
      patterns=[
          PostprocessingPattern(lambda ent: ent.text.lower() == "food resources"),
          (
                PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, r"NEED")),
                PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, r"ASSISTANCE")),
          ),

      ],
        action=set_ignored,
        value=False,
        description="Require 'food resources' to be modified by 'need' or 'assistance'"
    ),
    PostprocessingRule(
        patterns=[
            PostprocessingPattern(lambda ent: ent.label_ == "FOOD"),
            PostprocessingPattern(lambda ent: ent._.is_need),
            PostprocessingPattern(lambda ent: ent._.is_ignored is False),
            PostprocessingPattern(lambda ent: ent._.is_negated is True),
        ],
        action=postprocessing_functions.set_label,
        label="FOOD_SECURITY",
        description="Change 'denies any food needs' to 'FOOD_SECURITY'"
    ),

    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent: ent.label_ == "FOOD"),
    #         PostprocessingPattern(lambda ent: not any((ent._.is_negated, ent._.is_need, ent._.is_hypothetical, postprocessing_functions.is_modified_by_category(ent, "WORRY")))),
    #         PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, "SUFFICIENT")),
    #     ],
    #     action=postprocessing_functions.set_label,
    #     label="FOOD_INSECURITY",
    #     description="Replace 'worried about affording food' with 'food_insecurity'"
    # ),
    # PostprocessingRule(
    #     patterns=[
    #         PostprocessingPattern(lambda ent:ent.label_ in ("FOOD_SECURITY", "ACCESS")),
    #         PostprocessingPattern(lambda ent: postprocessing_functions.is_modified_by_category(ent, r"NO_ISSUE")),
    #     ],
    #     action=postprocessing_functions.set_label,
    #     label="FOOD_SECURITY"
    # )

]