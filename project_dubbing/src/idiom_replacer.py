import json
import re
import os

class IdiomReplacer:
    def __init__(self, idioms_path="idioms.json"):
        if not os.path.exists(idioms_path):
             # check up one directory if not found in current
            if os.path.exists(os.path.join("..", idioms_path)):
                 idioms_path = os.path.join("..", idioms_path)

        with open(idioms_path, "r") as f:
            self.idioms_data = json.load(f)
        
        self.idioms_dict = {item["idiom"].lower(): item["meaning"] for item in self.idioms_data}
        # Sort by length descending to match longest idioms first
        self.sorted_idioms = sorted(self.idioms_dict.keys(), key=len, reverse=True)

    def replace(self, sentence):
        """
        Replaces idioms in the given sentence with their meanings.
        """
        replaced_sentence = sentence
        
        for idiom in self.sorted_idioms:
            # Use regex for whole phrase matching (case insensitive)
            pattern = re.compile(r'\b' + re.escape(idiom) + r'\b', flags=re.IGNORECASE)
            if pattern.search(replaced_sentence):
                replaced_sentence = pattern.sub(self.idioms_dict[idiom], replaced_sentence)
        
        return replaced_sentence
