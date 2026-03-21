#!/usr/bin/env python3
"""
Generate images and music for LILIWATT promo video using fal.ai
"""
import os
import sys
import requests
import fal_client

os.environ["FAL_KEY"] = "c15ce4a8-5b09-4409-aec0-788670c796f6:4105df0b47f083155cd4e90b4c8f5f20"

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
IMG_OUT = os.path.join(BASE, "images", "generated")
os.makedirs(IMG_OUT, exist_ok=True)

# === GENERATE 5 IMAGES ===
images_prompts = [
    {
        "name": "restaurant",
        "prompt": "French restaurant owner looking worried at energy bill paper, cinematic dark purple lighting, premium corporate photography, color grade: deep navy shadows with purple highlights, photorealistic, 8k quality"
    },
    {
        "name": "boulanger",
        "prompt": "French baker in bakery checking electricity invoice paper, warm bread background, cinematic lighting, purple color grade, photorealistic, professional photography, 8k"
    },
    {
        "name": "conseiller",
        "prompt": "Professional energy consultant at modern desk with laptop, dark premium office, purple ambient lighting, confident smile, corporate photography, photorealistic, 8k"
    },
    {
        "name": "economie",
        "prompt": "Euro coins and bills with green upward arrow graph, dark background, purple and gold lighting, premium financial concept photography, 8k quality"
    },
    {
        "name": "contrat",
        "prompt": "Business handshake over energy contract documents on desk, dark premium office, purple violet ambient lighting, cinematic corporate photography, photorealistic, 8k"
    }
]

print("=" * 50)
print("LILIWATT — Génération des assets")
print("=" * 50)

# Generate images
for i, img_data in enumerate(images_prompts):
    print(f"\n[Image {i+1}/5] Génération : {img_data['name']}...")
    try:
        result = fal_client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": img_data["prompt"],
                "image_size": "landscape_16_9",
                "num_images": 1
            }
        )
        url = result["images"][0]["url"]
        print(f"  URL: {url}")

        # Download
        resp = requests.get(url)
        filepath = os.path.join(IMG_OUT, f"{img_data['name']}.png")
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"  Saved: {filepath}")
    except Exception as e:
        print(f"  ERROR: {e}")

# === GENERATE MUSIC ===
print(f"\n[Musique] Génération disco funk...")
try:
    result = fal_client.subscribe(
        "fal-ai/stable-audio",
        arguments={
            "prompt": "upbeat disco funk music, 70s style, energetic, professional corporate, groovy bassline, brass section, no lyrics, instrumental only, high quality production",
            "seconds_total": 30,
            "steps": 100
        }
    )
    music_url = result["audio_file"]["url"]
    print(f"  URL: {music_url}")

    resp = requests.get(music_url)
    music_path = os.path.join(BASE, "musique_disco.mp3")
    with open(music_path, "wb") as f:
        f.write(resp.content)
    print(f"  Saved: {music_path}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 50)
print("Assets générés !")
print("=" * 50)
