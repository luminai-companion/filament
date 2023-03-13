import os

import emoji
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

checkpoint = "vincentclaes/emoji-predictor"
x_, _, files = next(os.walk("./app/emojis"))
num_emojis = range(len(files))
emoji_images = [Image.open(f"./app/emojis/{i}.png") for i in num_emojis]

emoji_processor = CLIPProcessor.from_pretrained(checkpoint)
emoji_model = CLIPModel.from_pretrained(checkpoint)

# https://carpedm20.github.io/emoji/
predictor_emojis = [
    ":red_heart:",
    ":smiling_face_with_heart-eyes:",
    ":face_with_tears_of_joy:",
    ":two_hearts:",
    ":fire:",
    ":smiling_face_with_smiling_eyes:",
    ":smiling_face_with_sunglasses:",
    ":sparkles:",
    ":blue_heart:",
    ":face_blowing_a_kiss:",
    ":camera:",
    ":United_States:",
    ":sun:",
    ":purple_heart:",
    ":winking_face:",
    ":hundred_points:",
    ":beaming_face_with_smiling_eyes:",
    ":Christmas_tree:",
    ":camera_with_flash:",
    ":winking_face_with_tongue:",
    ":frowning_face:",
    ":loudly_crying_face:",
    ":disappointed_face:",
    ":enraged_face:",
    ":anger_symbol:",
    ":face_with_steam_from_nose:",
    ":flushed_face:",
    ":upside-down_face:",
    ":weary_face:",
    ":angry_face:",
    ":see-no-evil_monkey:",
    ":face_with_rolling_eyes:",
]


def predict_emojis(
    text, model=emoji_model, processor=emoji_processor, emojis=emoji_images, k=4
):
    inputs = processor(
        text=text, images=emojis, return_tensors="pt", padding=True, truncation=True
    )
    outputs = model(**inputs)

    logits_per_text = outputs.logits_per_text
    # we take the softmax to get the label probabilities
    p_tensor = logits_per_text.softmax(dim=1)

    predictions = [torch.topk(p, k).indices.tolist() for p in p_tensor][0]
    # probs = [torch.topk(p, k).values.tolist() for p in p_tensor][0]

    emoji_text = emoji.emojize("".join([predictor_emojis[i] for i in predictions]))

    return emoji_text
