
from config import DOMAIN_LABELS

def classify_domain(classifier, text):
    result = classifier(text, DOMAIN_LABELS)
    top_label = result["labels"][0]
    top_score = result["scores"][0]
    runner_up_score = result["scores"][1]
    gap = top_score - runner_up_score
    return top_label, top_score, gap

