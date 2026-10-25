from PIL import Image

user_img = Image.open(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\.user_uploaded\media_1792919016930_1f3f17fa.png").convert("RGB")
dump_bg1 = Image.open(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\dustdawn_dump\ui_activity_20104__bg_dustdawn_main_1.png").convert("RGB")
dump_story = Image.open(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\dustdawn_dump\ui_mainlineex_dustdawnstory__bg_dustdawn_story.png").convert("RGB")

u_thumb = user_img.resize((64, 64))
bg1_thumb = dump_bg1.resize((64, 64))
story_thumb = dump_story.resize((64, 64))

u_data = list(u_thumb.getdata())
bg1_data = list(bg1_thumb.getdata())
story_data = list(story_thumb.getdata())

diff_bg1 = sum(abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2]) for a, b in zip(u_data, bg1_data)) / (64*64*3)
diff_story = sum(abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2]) for a, b in zip(u_data, story_data)) / (64*64*3)

print(f"Diff with bg1: {diff_bg1:.2f}")
print(f"Diff with story: {diff_story:.2f}")

# Save thumbnails for visual check
u_thumb.save(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\thumb_user.png")
bg1_thumb.save(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\thumb_bg1.png")
story_thumb.save(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\thumb_story.png")
print("Saved thumbnails")
