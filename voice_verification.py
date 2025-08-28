from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np

import torchaudio
from speechbrain.inference.speaker import SpeakerRecognition

encoder = VoiceEncoder()
wav = preprocess_wav(Path("testing_files//Recording (2).wav"))
my_embed = encoder.embed_utterance(wav)

test_wav = preprocess_wav(Path("testing_files//Recording (4).wav"))
test_embed = encoder.embed_utterance(test_wav)

similarity = np.inner(my_embed, test_embed)
print("Similarity:", similarity)  # closer to 1 means same speaker


# # Load the pretrained speaker verification model
# verification = SpeakerRecognition.from_hparams(
#     source="speechbrain/spkrec-ecapa-voxceleb"
# )

# # Compare two audio files (enrollment vs test)
# score, prediction = verification.verify_files("testing_files//Recording (2).wav", "testing_files//Recording (4).wav")

# print(f"Score: {score}")
# print(f"Prediction: {prediction}")  # True if same speaker

