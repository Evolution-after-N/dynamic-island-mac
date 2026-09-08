from AppKit import NSApp, NSApplicationActivationPolicyAccessory
import tkinter as tk
from AppKit import NSApp
import subprocess
from PIL import Image, ImageTk, ImageDraw
import random
import threading
import time
import math
root = tk.Tk()
is_expanded = False
is_playing=True
bar_heights = [10, 10, 10, 10, 10]
album_image = None
latest_artist = ""
latest_song = ""
latest_art_image = None
album_image_large = None
data_lock = threading.Lock()
NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
root.overrideredirect(1)
root.wm_attributes("-topmost", True)
root.wm_attributes("-transparent", True)
screen_width = root.winfo_screenwidth()
island_centred = (screen_width - 280) // 2 
root.config(bg="systemTransparent")
canvas = tk.Canvas(root, width=280, height=90, bg="systemTransparent", highlightthickness=0)
canvas.pack()
root.geometry(f"280x90+{island_centred}+0")

#defining collapsed and expanded pill
def draw_collapsed_pill():
    canvas.delete("pill_bg")
    canvas.create_oval(0, 0, 36, 36, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_oval(244, 0, 280, 36, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_rectangle(18, 0, 262, 36, fill="#1a1a1a", outline="", tags="pill_bg")

def draw_expanded_pill():
    canvas.delete("pill_bg")
    canvas.create_rectangle(0, 0, 280, 90, fill="", outline="")  # keeps canvas bounds, invisible
    canvas.create_oval(0, 0, 36, 90, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_oval(244, 0, 280, 90, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_rectangle(18, 0, 262, 90, fill="#1a1a1a", outline="", tags="pill_bg")
# Left circle cap
canvas.create_oval(0, 0, 36, 36, fill="#1a1a1a", outline="")

# Right circle cap
canvas.create_oval(244, 0, 280, 36, fill="#1a1a1a", outline="")

# Middle rectangle connecting them
canvas.create_rectangle(18, 0, 262, 36, fill="#1a1a1a", outline="")
root.update_idletasks()
#reusable rounded bar func

def draw_rounded_bar(x, y1, y2, width, tags):
    radius = width / 2
    canvas.create_oval(x, y1, x+width, y1+width, fill="#ffffff", outline="", tags=tags)
    canvas.create_oval(x, y2-width, x+width, y2, fill="#ffffff", outline="", tags=tags)
    canvas.create_rectangle(x, y1+radius, x+width, y2-radius, fill="#ffffff", outline="", tags=tags)

#reusable rounded rectangle func
def draw_rounded_rect(x1, y1, x2, y2, radius, tags):
    canvas.create_oval(x1, y1, x1+radius*2, y1+radius*2, fill="#ffffff", outline="", tags=tags)
    canvas.create_oval(x2-radius*2, y1, x2, y1+radius*2, fill="#ffffff", outline="", tags=tags)
    canvas.create_rectangle(x1+radius, y1, x2-radius, y1+radius*2, fill="#ffffff", outline="", tags=tags)
#reusable rounded triangle func
def rounded_triangle_points(p1, p2, p3, radius, arc_steps=16):
    points = [p1, p2, p3]
    result = []

    for i in range(3):
        curr = points[i]
        prev_point = points[i-1]
        next_point = points[(i+1) % 3]

        dx1, dy1 = prev_point[0]-curr[0], prev_point[1]-curr[1]
        dist1 = math.hypot(dx1, dy1)
        u1 = (dx1/dist1, dy1/dist1)

        dx2, dy2 = next_point[0]-curr[0], next_point[1]-curr[1]
        dist2 = math.hypot(dx2, dy2)
        u2 = (dx2/dist2, dy2/dist2)

        angle_between = math.acos(max(-1, min(1, u1[0]*u2[0] + u1[1]*u2[1])))
        half_angle = angle_between / 2

        tangent_dist = radius / math.tan(half_angle)
        start = (curr[0] + u1[0]*tangent_dist, curr[1] + u1[1]*tangent_dist)
        end = (curr[0] + u2[0]*tangent_dist, curr[1] + u2[1]*tangent_dist)

        bisector_x = u1[0] + u2[0]
        bisector_y = u1[1] + u2[1]
        bisector_len = math.hypot(bisector_x, bisector_y)
        bisector = (bisector_x/bisector_len, bisector_y/bisector_len)

        center_dist = radius / math.sin(half_angle)
        center = (curr[0] + bisector[0]*center_dist, curr[1] + bisector[1]*center_dist)

        angle_start = math.atan2(start[1]-center[1], start[0]-center[0])
        angle_end = math.atan2(end[1]-center[1], end[0]-center[0])

        angle_diff = angle_end - angle_start
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        for step in range(arc_steps + 1):
            t = step / arc_steps
            angle = angle_start + angle_diff * t
            arc_x = center[0] + math.cos(angle) * radius
            arc_y = center[1] + math.sin(angle) * radius
            result.append((arc_x, arc_y))

    return result
#state for pause/play icon
def draw_play_button():
    canvas.delete("play_btn")
    if is_playing:
        # this is the mf pause icon
        draw_rounded_bar(130, 46, 74, 8, ("expanded_content", "play_btn"))
        draw_rounded_bar(146, 46, 74, 8, ("expanded_content", "play_btn"))

    else:
        #play icon?
        points = rounded_triangle_points((124, 44), (124, 76), (156, 60), 4, arc_steps=16)
        flat_points = [coord for point in points for coord in point]
        canvas.create_polygon(flat_points, smooth=False, fill="#ffffff", outline="", tags=("expanded_content", "play_btn"))
    canvas.tag_bind("play_btn", "<Button-1>", toggle_playback)
#animation ifier
def draw_expanded_content():
    canvas.create_rectangle(0, 18, 280, 72, fill="#1a1a1a", outline="", tags="expanded_content")
    canvas.create_oval(0, 54, 36, 90, fill="#1a1a1a", outline="", tags="expanded_content")
    canvas.create_oval(244, 54, 280, 90, fill="#1a1a1a", outline="", tags="expanded_content")
    canvas.create_rectangle(18, 72, 262, 90, fill="#1a1a1a", outline="", tags="expanded_content")

    draw_play_button()

    next_back = rounded_triangle_points((212, 44), (212, 76), (240, 60), 3.6, arc_steps=16)
    canvas.create_polygon([c for p in next_back for c in p], smooth=False, fill="#ffffff", outline="", tags=("expanded_content", "next_btn"))
    next_front = rounded_triangle_points((236, 44), (236, 76), (271, 60), 3.6, arc_steps=16)
    canvas.create_polygon([c for p in next_front for c in p], smooth=False, fill="#ffffff", outline="", tags=("expanded_content", "next_btn"))

    prev_back = rounded_triangle_points((68, 44), (68, 76), (40, 60), 3.6, arc_steps=16)
    canvas.create_polygon([c for p in prev_back for c in p], smooth=False, fill="#ffffff", outline="", tags=("expanded_content", "prev_btn"))
    prev_front = rounded_triangle_points((44, 44), (44, 76), (9, 60), 3.6, arc_steps=16)
    canvas.create_polygon([c for p in prev_front for c in p], smooth=False, fill="#ffffff", outline="", tags=("expanded_content", "prev_btn"))

    canvas.tag_bind("prev_btn", "<Button-1>", previous_track)
    canvas.tag_bind("next_btn", "<Button-1>", next_track)

    canvas.tag_raise("album_art")
    canvas.tag_raise("song_text")
    canvas.tag_raise("eq_bar")
    

def animate_expand(step=0, steps=12):
    h = 36 + (90 - 36) * (step / steps)
    canvas.delete("pill_bg")
    canvas.create_oval(0, 0, 36, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_oval(244, 0, 280, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_rectangle(18, 0, 262, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.tag_lower("pill_bg")
    if step < steps:
        root.after(15, lambda: animate_expand(step + 1, steps))
    else:
        draw_expanded_content()

def animate_collapse(step=0, steps=12):
    h = 90 - (90 - 36) * (step / steps)
    canvas.delete("pill_bg")
    canvas.create_oval(0, 0, 36, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_oval(244, 0, 280, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.create_rectangle(18, 0, 262, h, fill="#1a1a1a", outline="", tags="pill_bg")
    canvas.tag_lower("pill_bg")
    if step < steps:
        root.after(15, lambda: animate_collapse(step + 1, steps))
#equalizer barssss
bar_positions = [250, 253, 256, 259, 262]

def animate_bars():
    canvas.delete("eq_bar")

    for i, x in enumerate(bar_positions):
        if is_playing:
            target = random.randint(4, 20)
        else:
            target = 2

        current = bar_heights[i]
        bar_heights[i] = current + (target - current) * 0.25

        height = bar_heights[i]
        top = 18 - (height / 2)
        bottom = 18 + (height / 2)
        canvas.create_rectangle(x, top, x+1, bottom, fill="#ffffff", outline="", tags="eq_bar")

    root.after(150, animate_bars)
animate_bars()
def on_click(event):
    global is_expanded

    if event.y > 36:
        return
    is_expanded = not is_expanded

    if is_expanded:
        animate_expand()
    else:
        canvas.delete("expanded_content")
        animate_collapse()

canvas.bind("<Button-1>", on_click)
#gets the album art for the pill
def save_album_art():
    script = '''
    tell application "Music"
        set artData to data of artwork 1 of current track
    end tell
    set outputFile to (POSIX path of (path to home folder)) & "cover.jpg"
    set fileRef to open for access outputFile with write permission
    set eof fileRef to 0
    write artData to fileRef
    close access fileRef
    '''

    with open("temp_script.applescript", "w") as f:
        f.write(script)

    result = subprocess.run(["osascript", "temp_script.applescript"], capture_output=True, text=True)
#presents the image to tkinter +  rounds corners
def load_album_art():
    image = Image.open("/Users/noah/cover.jpg")
    image = image.resize((24, 24), Image.LANCZOS)
    image = image.convert("RGBA")

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 24, 24), radius=6, fill=255)

    image.putalpha(mask)

    return ImageTk.PhotoImage(image)
# Gets current Song and textifies it
def background_worker():
    global latest_artist, latest_song, latest_art_image

    while True:
        try:
            save_album_art()
            image = Image.open("/Users/noah/cover.jpg")
            image = image.resize((24, 24), Image.LANCZOS)
            image = image.convert("RGBA")
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, 24, 24), radius=6, fill=255)
            image.putalpha(mask)

            artist, song = get_current_song()

            with data_lock:
                latest_artist = artist
                latest_song = song
                latest_art_image = image
        except Exception as e:
            print("Background error:", e)

        time.sleep(1)

def get_current_song():
    script = 'tell application "Music" to get {artist of current track, name of current track}'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    output = result.stdout.strip()
    artist, song = output.split(", ", 1)
    return artist, song
def update_display():
    global album_image
    canvas.delete("song_text")
    canvas.delete("album_art")

    with data_lock:
        artist = latest_artist
        song = latest_song
        art = latest_art_image

    if art is not None:
        album_image = ImageTk.PhotoImage(art)
        canvas.create_image(22, 18, image=album_image, tags="album_art")

    canvas.create_text(140, 12, text=song, fill="#ffffff", font=("SF Pro", 10), tags="song_text")
    canvas.create_text(140, 24, text=f"-{artist}", fill="#999999", font=("SF Pro", 8), tags="song_text")
    root.after(200, update_display)

 #playbuttons
def toggle_playback(event=None):
        global is_playing
        subprocess.run(["osascript", "-e", 'tell application "Music" to playpause'])
        is_playing = not is_playing
        draw_play_button()
def animate_button_press(tag, cx, cy):
    canvas.scale(tag, cx, cy, 0.9, 0.9)
    root.after(80, lambda: canvas.scale(tag, cx, cy, 1/0.9, 1/0.9))

def next_track(event=None):
    animate_button_press("next_btn", 241.5, 60)
    root.after(50, lambda: subprocess.run(["osascript", "-e", 'tell application "Music" to next track']))

def previous_track(event=None):
    animate_button_press("prev_btn", 38.5, 60)
    root.after(50, lambda: subprocess.run(["osascript", "-e", 'tell application "Music" to previous track']))

update_display()
 # helps make fullscreen possible
def set_window_behavior():
    for window in NSApp.windows():
        if window.title() == "tk":
            window.setCollectionBehavior_((1 << 0) | (1 << 8))
            window.setLevel_(2147483647)

root.after(100, set_window_behavior)
#creates a thread for background worker--with kill switch for if porgram closes
thread = threading.Thread(target=background_worker, daemon=True)
thread.start()

root.mainloop()