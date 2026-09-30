import os
import torch
import numpy as np
from PIL import Image
from ingestion.pdf_to_images import render_page_as_image
from transformers import ColQwen2ForRetrieval, ColQwen2Processor


def embed_and_save_page(image, output_path, model, processor):
    inputs = processor(images=[image]).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = outputs.embeddings
    page_embedding = embedding[0]
    page_embedding_np = page_embedding.float().cpu().numpy()

    np.save(output_path, page_embedding_np)


def embed_all_pages(pdf_path, num_pages, image_dir, embedding_dir, model, processor):
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(embedding_dir, exist_ok=True)

    for page_number in range(1, num_pages + 1):
        image_filename = f"page_{page_number:03d}.png"
        embedding_filename = f"page_{page_number:03d}.npy"
        image_path = os.path.join(image_dir, image_filename)
        embedding_path = os.path.join(embedding_dir, embedding_filename)

        print(f"Page {page_number}/{num_pages}: rendering...")
        render_page_as_image(pdf_path, page_number - 1, image_path)

        image = Image.open(image_path)

        print(f"Page {page_number}/{num_pages}: embedding...")
        embed_and_save_page(image, embedding_path, model, processor)

        print(f"Page {page_number}/{num_pages}: done")

def embed_query(query_text, model, processor):
    inputs = processor(text=[query_text]).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)

    query_embedding = outputs.embeddings[0]
    query_embedding_np = query_embedding.float().cpu().numpy()

    return query_embedding_np

def maxsim_score(query_embedding, page_embedding):
    similarity_matrix = query_embedding @ page_embedding.T
    max_similarities = similarity_matrix.max(axis=1)
    return max_similarities.sum()

def rank_pages(query_embedding, embedding_dir, num_pages, first_page=1, last_page=None):
    scores = []
    last = last_page or num_pages

    for page_number in range(first_page, last + 1):
        filename = f"page_{page_number:03d}.npy"
        path = os.path.join(embedding_dir, filename)
        page_embedding = np.load(path)

        score = maxsim_score(query_embedding, page_embedding)
        scores.append((page_number, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

from transformers import ColQwen2ForRetrieval, ColQwen2Processor

def load_colqwen2_model(model_name="vidore/colqwen2-v1.0-hf"):
    model = ColQwen2ForRetrieval.from_pretrained(model_name, device_map="auto").eval()
    processor = ColQwen2Processor.from_pretrained(model_name)
    return model, processor

if __name__ == "__main__":
    model, processor = load_colqwen2_model()

    embed_all_pages(
        pdf_path="apple_10k.pdf",
        num_pages=61,
        image_dir="ingestion/page_images",
        embedding_dir="vectorstore/colpali_embeddings",
        model=model,
        processor=processor,
    )