import pandas as pd
from datasets import Dataset, ClassLabel, Features, Sequence, Value
from transformers import BertTokenizerFast, BertForTokenClassification, TrainingArguments, Trainer
import torch

# 1. Define Entity Labels
# We'll use IOB (Inside, Outside, Beginning) format
labels = ["O", "B-CPU", "I-CPU", "B-RAM", "I-RAM", "B-DISK", "I-DISK"]
id_to_label = {i: label for i, label in enumerate(labels)}
label_to_id = {label: i for i, label in enumerate(labels)}
num_labels = len(labels)

print(f"Defined {num_labels} labels: {labels}")

# 2. Prepare Training Data (Replace with your actual data loading)
# Assume your data is a list of dictionaries or a pandas DataFrame
# Each item/row should have 'title', 'description', 'cpu', 'ram', 'disk'
# Example data structure (replace with your actual data loading logic)
training_data = [
    {
        "title": "Dell Inspiron 15 3000 Laptop",
        "description": "Intel Core i5-1135G7, 8GB DDR4 RAM, 512GB NVMe SSD, 15.6 inch display.",
        "cpu": "Intel Core i5-1135G7",
        "ram": "8GB DDR4 RAM",
        "disk": "512GB NVMe SSD"
    },
    {
        "title": "HP Pavilion Gaming Laptop",
        "description": "AMD Ryzen 7 5800H, 16GB RAM, 1TB HDD + 256GB SSD, GeForce RTX 3060.",
        "cpu": "AMD Ryzen 7 5800H",
        "ram": "16GB RAM",
        "disk": "1TB HDD + 256GB SSD"
    },
     {
        "title": "Lenovo IdeaPad Slim 3",
        "description": "Intel Celeron N4020 processor, 4GB RAM, 128GB eMMC storage, 14 inch HD.",
        "cpu": "Intel Celeron N4020",
        "ram": "4GB RAM",
        "disk": "128GB eMMC storage"
    },
    # Add many more samples here... ideally hundreds or thousands
]

# Convert to pandas DataFrame (optional, but convenient)
df = pd.DataFrame(training_data)

# Combine title and description (add a separator token for clarity)
# BERT was trained with [SEP], so it's a good separator.
df['text'] = df['title'] + " [SEP] " + df['description']

print(f"\nLoaded {len(df)} training samples.")
print("Example combined text:", df['text'].iloc[0])

# 3. Tokenization and Label Alignment

# Load the tokenizer
model_checkpoint = "bert-base-uncased" # You can try other models like 'roberta-base'
tokenizer = BertTokenizerFast.from_pretrained(model_checkpoint)

# Function to align tokens with labels
def align_labels_with_tokens(tokens, word_ids, entity_strings):
    """
    Aligns entity labels (IOB format) to tokens, considering word splits.
    entity_strings should be a dictionary like {'cpu': '...', 'ram': '...', 'disk': '...'}
    """
    label_ids = []
    previous_word_idx = None
    current_tags = {key: None for key in entity_strings.keys()} # Track if we are inside an entity of this type

    # Lowercase entity strings for case-insensitive matching
    lower_entity_strings = {k: v.lower() for k, v in entity_strings.items()}
    lower_text = " ".join(tokens).replace(" ##", "").lower() # Approximate lowercased text to find entities

    for word_idx in word_ids:
        if word_idx is None:
            # Special tokens ([CLS], [SEP], [PAD]) get -100, ignored in loss
            label_ids.append(-100)
        elif word_idx != previous_word_idx:
            # We are at the start of a new word
            tag_assigned = False
            # Check if this word starts one of our target entities
            # This simple implementation checks if the word is part of a known entity string span
            # A more robust implementation would involve matching word sequences to entity strings
            # Let's simplify: Check if the *original* text span this word_idx corresponds to
            # is part of one of the entity strings. This requires offset mapping,
            # but we can approximate by checking if the entity string is found in the original text
            # and if this word is within that span.

            # A better approach for word-level entities:
            # Get the original words corresponding to the word_ids
            original_words = []
            current_word_tokens = []
            for i, w_id in enumerate(word_ids):
                if w_id is not None:
                     if previous_word_idx != w_id:
                         if current_word_tokens:
                            original_words.append(tokenizer.decode(current_word_tokens))
                         current_word_tokens = [tokens[i]]
                     else:
                         current_word_tokens.append(tokens[i])
                else:
                     if current_word_tokens:
                        original_words.append(tokenizer.decode(current_word_tokens))
                        current_word_tokens = []
                     original_words.append(tokenizer.decode(tokens[i])) # Handle special tokens


            # This simple approach of checking if the entity string is *in* the text
            # and then tagging based on word index might be inaccurate with subwords
            # and complex phrases.
            # Let's refine the tagging logic:

            # Reset 'inside' tags for the new word
            for key in current_tags:
                 current_tags[key] = None # Not inside anymore unless we start a *new* entity

            # Find which entity this word belongs to based on original text span
            word_text = tokenizer.decode(tokens[tokenizer.word_to_tokens(word_idx)[0]: tokenizer.word_to_tokens(word_idx)[-1]+1]) # Text of the current word (might be partial due to ##)
            # Find the start character index of this word in the original combined text
            # This is complex without offset_mapping. Let's rely on simpler string matching for words first.

            # A more practical approach for training data generation:
            # Iterate through original words in the text.
            # For each original word, check if it's part of an entity string.
            # If it is, assign B- or I- tag to *all* tokens corresponding to that word.

            # Let's rewrite the data processing to align words first, then tokens.

            label_ids.append(label_to_id["O"]) # Default to O for now
        else:
            # Same word as previous token (likely a subword)
            # Assign the same tag as the previous token
            label_ids.append(label_ids[-1]) # Propagate the tag from the first token of the word

        previous_word_idx = word_idx

    # The above word_ids logic is standard but aligning entities based on simple strings is tricky.
    # A robust NER dataset preparation needs careful alignment using character offsets or
    # matching the original word sequence.

    # Let's implement a common pattern using the tokenizer's ability to map back to words
    # and match against the provided entity strings.

    return label_ids # This needs to be filled correctly


# --- Revised Data Processing Function ---

def process_sample(sample):
    """Tokenizes text and aligns labels for a single sample."""
    text = sample['text']
    # Use return_offsets_mapping=True to map tokens back to character spans
    # Use return_word_ids=True to map tokens back to original words
    encoded_input = tokenizer(text,
                              is_split_into_words=False, # Process as single text string
                              return_offsets_mapping=True,
                              return_word_ids=True,
                              padding="max_length", # Pad or truncate for batching
                              truncation=True,
                              max_length=512 # Max length for BERT
                             )

    # Get the original word IDs for each token
    word_ids = encoded_input.word_ids()
    # Get the character offsets for each token
    offset_mapping = encoded_input.offset_mapping

    # Initialize labels list with ignore index for special tokens/padding
    labels = [-100] * len(word_ids)

    # Lowercase entity strings for matching
    entities = {
        'CPU': sample['cpu'].lower() if pd.notna(sample['cpu']) else '',
        'RAM': sample['ram'].lower() if pd.notna(sample['ram']) else '',
        'DISK': sample['disk'].lower() if pd.notna(sample['disk']) else ''
    }

    # Lowercase the original text for matching
    lower_text = text.lower()

    # Find the start and end char indices of each entity in the lowercased text
    entity_spans = {}
    for entity_type, entity_text in entities.items():
        if entity_text:
            # Find all occurrences of the entity text in the original text
            start = 0
            while True:
                start = lower_text.find(entity_text, start)
                if start == -1:
                    break
                end = start + len(entity_text)
                entity_spans.setdefault(entity_type, []).append((start, end))
                start = end # Continue search after this match


    # Assign labels to tokens based on character offsets and entity spans
    previous_word_idx = None
    for token_idx, word_idx in enumerate(word_ids):
        if word_idx is None:
            # Special tokens already have -100
            continue

        # Get the character span for the current token in the original text
        token_char_start, token_char_end = offset_mapping[token_idx]

        if previous_word_idx != word_idx:
            # This is the first token of a new word
            # Check if this word (or subsequent tokens of this word) overlaps with any entity span
            # We need to find which entity the *entire original word* belongs to.
            # Get the character span for the entire word
            word_token_span = tokenizer.word_to_tokens(word_idx) # (start_token_idx, end_token_idx)
            if word_token_span is not None:
                 word_char_start, word_char_end = offset_mapping[word_token_span[0]][0], offset_mapping[word_token_span[1]][1]

                 # Find the entity type this word belongs to
                 word_entity_type = None
                 for entity_type, spans in entity_spans.items():
                     for span_start, span_end in spans:
                         # Check if the word span is fully contained within an entity span
                         if word_char_start >= span_start and word_char_end <= span_end:
                            word_entity_type = entity_type
                            break # Found the entity for this word
                     if word_entity_type: break # Found entity for this word, move to next word

                 if word_entity_type:
                     # This word starts an entity
                     labels[token_idx] = label_to_id[f"B-{word_entity_type}"]
                 else:
                     # This word is not part of any entity
                     labels[token_idx] = label_to_id["O"]
            else:
                # Should not happen for non-None word_ids with Fast tokenizers, but handle defensively
                labels[token_idx] = label_to_id["O"]

        else:
            # This token belongs to the same word as the previous token (it's a subword)
            # Assign the same tag as the first token of the word (which was handled above)
            # We need the tag of the *first* token of this word.
            # A simpler way with word_ids: Check the label assigned to the token with the same word_id
            first_token_of_word_idx = tokenizer.word_to_tokens(word_idx)[0]
            labels[token_idx] = labels[first_token_of_word_idx]


        previous_word_idx = word_idx

    encoded_input['labels'] = labels
    # Remove offset_mapping and word_ids as they are not needed for the model input
    del encoded_input['offset_mapping']
    del encoded_input['word_ids']

    return encoded_input

# Apply the processing function to your DataFrame
# Note: For a real dataset, you'd likely load it into a `datasets.Dataset` object
# directly and use its `map` method, which is more efficient.
# Let's create a datasets.Dataset from the dataframe
hf_dataset = Dataset.from_pandas(df)

# Define features for the dataset for clarity and type safety
features = Features({
    'title': Value('string'),
    'description': Value('string'),
    'cpu': Value('string'),
    'ram': Value('string'),
    'disk': Value('string'),
    'text': Value('string'), # Combined text
    'input_ids': Sequence(Value('int32')),
    'token_type_ids': Sequence(Value('int8')), # For BERT
    'attention_mask': Sequence(Value('int8')),
    'labels': Sequence(Value('int64')), # Labels aligned to tokens
})


# Process the dataset (apply the processing function)
# Use batched=True for efficiency if process_sample was designed for batches
# Here, process_sample handles one sample, so batched=False
processed_dataset = hf_dataset.map(process_sample, features=features, remove_columns=['title', 'description', 'cpu', 'ram', 'disk', 'text']) # Remove original text columns

print("\nProcessed dataset features:", processed_dataset.features)
print("Example processed sample:", processed_dataset[0])
print("Example processed sample labels:", processed_dataset[0]['labels'])
print("Example label mapping:", [id_to_label[l] if l != -100 else "IGNORE" for l in processed_dataset[0]['labels']])


# 4. Split data (optional but recommended)
# For a small example, we won't split. For real training, split into train/validation/test.
# e.g., train_dataset = processed_dataset.train_test_split(test_size=0.1)['train']
#       eval_dataset = processed_dataset.train_test_split(test_size=0.1)['test']
train_dataset = processed_dataset # Using all data for training in this simple example

# 5. Load the Model
model = BertForTokenClassification.from_pretrained(model_checkpoint, num_labels=num_labels, id2label=id_to_label, label2id=label_to_id)

# Check if GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"\nUsing device: {device}")

# 6. Define Training Arguments
output_dir = "./results" # Directory to save model checkpoints and logs

training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch", # Evaluate at the end of each epoch (if eval_dataset provided)
    learning_rate=2e-5,
    per_device_train_batch_size=16, # Adjust based on GPU memory
    per_device_eval_batch_size=16,
    num_train_epochs=3, # Number of training epochs
    weight_decay=0.01,
    logging_dir=f"{output_dir}/logs",
    logging_steps=10, # Log every 10 steps
    push_to_hub=False, # Set to True if you want to push to HF Hub
    report_to="none" # Don't report to external services like W&B
)

# Add a dummy evaluation dataset if you skipped splitting earlier
# or remove the evaluation_strategy if you truly have no eval data
# For this example, let's use the train data also for 'evaluation' to make the trainer run
# In real code, use a separate evaluation set!
eval_dataset = train_dataset


# 7. Define Metrics (Optional but Good Practice)
# For NER, you'd typically use precision, recall, F1 score per entity type.
# This requires converting predictions (logits) to tags and handling IOB format.
# The seqeval library is common for this.
# For simplicity in this basic code, we skip defining a custom compute_metrics.
# The default trainer evaluation will likely just compute loss.

# def compute_metrics(eval_pred):
#     logits, labels = eval_pred
#     predictions = np.argmax(logits, axis=-1)
#     # Flatten predictions and labels, ignoring -100
#     true_labels = [[id_to_label[l] for l in label if l != -100] for label in labels]
#     true_predictions = [[id_to_label[p] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in zip(predictions, labels)]
#     # Use seqeval (requires import)
#     results = seqeval.evaluate(true_labels, true_predictions)
#     return {
#         "precision": results["overall_precision"],
#         "recall": results["overall_recall"],
#         "f1": results["overall_f1"],
#         "accuracy": results["overall_accuracy"],
#     }


# 8. Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset, # Use a real eval set here
    tokenizer=tokenizer, # Pass tokenizer to handle padding in batches
    # compute_metrics=compute_metrics # Add this if you implement compute_metrics
)

# 9. Train the Model
print("\nStarting training...")
trainer.train()
print("Training finished.")

# 10. Save the Model
trainer.save_model(f"{output_dir}/final_model")
print(f"\nModel saved to {output_dir}/final_model")

# --- Post-Training: How to Use the Model for Prediction ---

# This part is for *inference* after training.
# Loading the trained model
loaded_model = BertForTokenClassification.from_pretrained(f"{output_dir}/final_model")
loaded_tokenizer = BertTokenizerFast.from_pretrained(f"{output_dir}/final_model") # Tokenizer is also saved

# Move model to device
loaded_model.to(device)
loaded_model.eval() # Set model to evaluation mode

def extract_features(text, model, tokenizer, id_to_label):
    """Extracts features (CPU, RAM, Disk) from text using the trained NER model."""
    # Tokenize input text
    encoding = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)

    # Get predictions (logits)
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
    logits = outputs.logits

    # Get predicted token IDs
    predictions = torch.argmax(logits, dim=-1).squeeze().tolist() # Squeeze removes batch dimension if batch_size=1

    # Get original tokens (helpful for mapping back)
    tokens = tokenizer.convert_ids_to_tokens(input_ids.squeeze().tolist())

    # Get word IDs to map tokens back to original words
    word_ids = encoding.word_ids(batch_index=0) # Use batch_index=0 for the first sample

    # Convert predicted IDs to labels (tags)
    predicted_labels = [id_to_label[p] if p != -100 else "IGNORE" for p in predictions]

    # --- Post-processing: Extract entity text from tokens and tags ---
    extracted_features = {"cpu": None, "ram": None, "disk": None}
    current_entity_type = None
    current_entity_tokens = []
    current_entity_word_ids = [] # Track word IDs for the current entity

    # Iterate through tokens and their predicted labels
    for i, (token, label, word_id) in enumerate(zip(tokens, predicted_labels, word_ids)):
        if word_id is None or label == "IGNORE": # Skip special tokens and padding
            if current_entity_type: # If we were in an entity, end it
                entity_text = tokenizer.decode([tokens[j] for j in current_entity_word_ids if tokens[j] not in tokenizer.all_special_tokens]).strip() # Decode words based on their first token index
                if extracted_features[current_entity_type.lower()] is None: # Only take the first occurrence
                    extracted_features[current_entity_type.lower()] = entity_text
                current_entity_type = None
                current_entity_tokens = []
                current_entity_word_ids = []
            continue

        # Check if this token starts a new entity
        if label.startswith("B-"):
            if current_entity_type: # If we were already in an entity, the previous one ended
                 entity_text = tokenizer.decode([tokens[j] for j in current_entity_word_ids if tokens[j] not in tokenizer.all_special_tokens]).strip()
                 if extracted_features[current_entity_type.lower()] is None:
                     extracted_features[current_entity_type.lower()] = entity_text

            current_entity_type = label.split("-")[1]
            current_entity_tokens = [token]
            # Use the index of the *first* token of the word
            current_entity_word_ids = [tokenizer.word_to_tokens(word_id)[0]]
        # Check if this token is inside the current entity
        elif label.startswith("I-") and current_entity_type and label.split("-")[1] == current_entity_type:
             # Only add the token if it's the first token of a new word within the entity
             if word_id != (current_entity_word_ids[-1] if current_entity_word_ids else None):
                  current_entity_word_ids.append(tokenizer.word_to_tokens(word_id)[0])
        else: # Label is "O" or starts a different entity, and we were in an entity
            if current_entity_type:
                entity_text = tokenizer.decode([tokens[j] for j in current_entity_word_ids if tokens[j] not in tokenizer.all_special_tokens]).strip()
                if extracted_features[current_entity_type.lower()] is None:
                    extracted_features[current_entity_type.lower()] = entity_text
                current_entity_type = None
                current_entity_tokens = []
                current_entity_word_ids = []

    # Handle case where the last tokens were part of an entity
    if current_entity_type:
         entity_text = tokenizer.decode([tokens[j] for j in current_entity_word_ids if tokens[j] not in tokenizer.all_special_tokens]).strip()
         if extracted_features[current_entity_type.lower()] is None:
              extracted_features[current_entity_type.lower()] = entity_text


    # A simpler post-processing using predicted word indices:
    extracted_spans = {}
    current_entity_type = None
    current_span_word_ids = []

    for token_idx, (label, word_id) in enumerate(zip(predicted_labels, word_ids)):
         if word_id is None or label == "IGNORE":
              # End current span if active
              if current_entity_type and current_span_word_ids:
                  first_token_idx = tokenizer.word_to_tokens(current_span_word_ids[0])[0]
                  last_token_idx = tokenizer.word_to_tokens(current_span_word_ids[-1])[-1]
                  span_text = tokenizer.decode(input_ids.squeeze()[first_token_idx:last_token_idx+1])
                  extracted_spans[current_entity_type.lower()] = span_text
              current_entity_type = None
              current_span_word_ids = []
              continue # Skip special tokens

         # Check for B- tag starting a new entity
         if label.startswith("B-"):
             # End previous entity if active
             if current_entity_type and current_span_word_ids:
                 first_token_idx = tokenizer.word_to_tokens(current_span_word_ids[0])[0]
                 last_token_idx = tokenizer.word_to_tokens(current_span_word_ids[-1])[-1]
                 span_text = tokenizer.decode(input_ids.squeeze()[first_token_idx:last_token_idx+1])
                 extracted_spans[current_entity_type.lower()] = span_text

             # Start new entity
             current_entity_type = label.split("-")[1]
             current_span_word_ids = [word_id]

         # Check for I- tag continuing the current entity
         elif label.startswith("I-") and current_entity_type and label.split("-")[1] == current_entity_type:
             # Add word_id only if it's a new word and consecutive to the last word in the span
             # This check is simplified; true consecutiveness requires looking at original text structure or token indices.
             # A basic check: if the current word_id is the next in sequence after the last one
             if current_span_word_ids and word_id == current_span_word_ids[-1] + 1:
                 current_span_word_ids.append(word_id)
             # Or simply add the word_id if it's the first token of this word
             elif word_id not in current_span_word_ids and token_idx == tokenizer.word_to_tokens(word_id)[0]:
                  current_span_word_ids.append(word_id)

         else: # O tag or wrong I- tag
             # End current entity if active
             if current_entity_type and current_span_word_ids:
                 first_token_idx = tokenizer.word_to_tokens(current_span_word_ids[0])[0]
                 last_token_idx = tokenizer.word_to_tokens(current_span_word_ids[-1])[-1]
                 span_text = tokenizer.decode(input_ids.squeeze()[first_token_idx:last_token_idx+1])
                 extracted_spans[current_entity_type.lower()] = span_text
             current_entity_type = None
             current_span_word_ids = []

    # Handle entity at the end of the sequence
    if current_entity_type and current_span_word_ids:
        first_token_idx = tokenizer.word_to_tokens(current_span_word_ids[0])[0]
        last_token_idx = tokenizer.word_to_tokens(current_span_word_ids[-1])[-1]
        span_text = tokenizer.decode(input_ids.squeeze()[first_token_idx:last_token_idx+1])
        extracted_spans[current_entity_type.lower()] = span_text


    # Final formatting to match the desired JSON keys
    final_json_output = {
        "cpu": extracted_spans.get("cpu", None),
        "ram": extracted_spans.get("ram", None),
        "disk": extracted_spans.get("disk", None)
    }

    return final_json_output

# Example Usage after training
print("\nTesting extraction on a sample text:")
sample_text = "High-performance gaming laptop with Intel Core i9-13900H processor, 32GB DDR5 RAM, and a massive 2TB NVMe SSD."
extracted_data = extract_features(sample_text, loaded_model, loaded_tokenizer, id_to_label)
import json
print(json.dumps(extracted_data, indent=4))

sample_text_2 = "Budget laptop: AMD Athlon Silver 3050U, 4GB RAM, 128GB SSD"
extracted_data_2 = extract_features(sample_text_2, loaded_model, loaded_tokenizer, id_to_label)
print(json.dumps(extracted_data_2, indent=4))