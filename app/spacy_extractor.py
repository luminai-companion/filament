from dataclasses import dataclass
from typing import Dict, Iterable
from spacy.language import Language


@dataclass
class SpacyExtractor:
    """Encapsulates logic to pipe Records with an id and text body
    through a spacy model and return entities separated by Entity Type
    """

    nlp: Language
    doc_id_key: str = "id"
    doc_text_key: str = "text"

    def name_to_id(self, text: str) -> str:
        return text.lower().replace(" ", "-")

    def extract_entities(self, records: Iterable[Dict[str, str]]) -> list:
        """Return a list of dictionaries with extracted entities and their document's ID
        from an iterable of "document" dictionaries each with an `id` and `text` property
        """
        ids = texts = []
        for doc in records:
            ids.append(doc[self.doc_id_key])
            texts.append(doc[self.doc_text_key])

        result = []
        for doc_id, spacy_doc in zip(ids, self.nlp.pipe(texts)):
            entities = {}
            for ent in spacy_doc.ents:
                # Could use explaining why these values can be None and what happens here
                ent_id = ent.kb_id or ent.ent_id or self.name_to_id(ent.text)
                if ent_id not in entities:
                    ent_name = ent.text.capitalize() if ent.text.islower() else ent.text
                    entities[ent_id] = {
                        "name": ent_name,
                        "label": ent.label_,
                        "matches": [],
                    }
                entities[ent_id]["matches"].append(
                    {"start": ent.start_char, "end": ent.end_char, "text": ent.text}
                )

            result.append({"id": doc_id, "entities": list(entities.values())})
        return result
