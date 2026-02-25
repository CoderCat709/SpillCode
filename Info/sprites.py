import pygame
import os
from pathlib import Path

class AnimationFrame:
    """Represents a single frame in an animation"""
    def __init__(self, image, duration=100):
        self.image = image
        self.duration = duration  # milliseconds


class Animation:
    """Manages sprite animations"""
    def __init__(self, frames, loop=True):
        """
        frames: list of AnimationFrame objects
        loop: whether animation should loop
        """
        self.frames = frames
        self.loop = loop
        self.current_frame = 0
        self.elapsed_time = 0
        self.is_playing = True
        self.is_finished = False

    def update(self, dt):
        """Update animation based on elapsed time (dt in milliseconds)"""
        if not self.is_playing or not self.frames:
            return

        self.elapsed_time += dt
        current_frame_duration = self.frames[self.current_frame].duration

        if self.elapsed_time >= current_frame_duration:
            self.elapsed_time -= current_frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_playing = False
                    self.is_finished = True

    def get_current_image(self):
        """Get the current frame image"""
        if not self.frames:
            return None
        return self.frames[self.current_frame].image

    def reset(self):
        """Reset animation to start"""
        self.current_frame = 0
        self.elapsed_time = 0
        self.is_playing = True
        self.is_finished = False

    def pause(self):
        self.is_playing = False

    def play(self):
        self.is_playing = True


class Character:
    """Represents a character with animations and static images"""
    def __init__(self, name, idle_animation=None, idle_image=None, width=50, height=50):
        """
        name: character name
        idle_animation: Animation object for idle state
        idle_image: Static image for idle state (fallback if no animation)
        width, height: display dimensions
        """
        self.name = name
        self.animations = {}
        self.current_animation = None
        self.idle_animation = idle_animation
        self.idle_image = idle_image
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

        if idle_animation:
            self.current_animation = idle_animation

    def add_animation(self, state_name, animation):
        """Add a named animation (e.g., 'walk', 'jump', 'run')"""
        self.animations[state_name] = animation

    def set_animation(self, state_name):
        """Switch to a named animation"""
        if state_name in self.animations:
            self.current_animation = self.animations[state_name]
            self.current_animation.reset()
        elif state_name == 'idle' and self.idle_animation:
            self.current_animation = self.idle_animation
            self.current_animation.reset()

    def update(self, dt):
        """Update current animation"""
        if self.current_animation:
            self.current_animation.update(dt)

    def draw(self, surface):
        """Draw character on surface"""
        image = None
        
        if self.current_animation:
            image = self.current_animation.get_current_image()
        elif self.idle_image:
            image = self.idle_image

        if image:
            scaled_image = pygame.transform.scale(image, (self.width, self.height))
            surface.blit(scaled_image, (self.x, self.y))


class Background:
    """Represents a background image or animated background"""
    def __init__(self, name, animation=None, static_image=None):
        """
        name: background name
        animation: Animation object for animated background
        static_image: Static image for background (fallback if no animation)
        """
        self.name = name
        self.animation = animation
        self.static_image = static_image
        self.current_animation = animation

    def set_animation(self, animation):
        """Change the background animation"""
        self.current_animation = animation
        if animation:
            animation.reset()

    def update(self, dt):
        """Update background animation"""
        if self.current_animation:
            self.current_animation.update(dt)

    def draw(self, surface):
        """Draw background on surface"""
        image = None

        if self.current_animation:
            image = self.current_animation.get_current_image()
        elif self.static_image:
            image = self.static_image

        if image:
            scaled_image = pygame.transform.scale(image, surface.get_size())
            surface.blit(scaled_image, (0, 0))


class SpriteManager:
    """Manages all characters and backgrounds"""
    def __init__(self, assets_folder="Assets"):
        self.assets_folder = assets_folder
        self.characters = {}
        self.backgrounds = {}
        self.current_character = None
        self.current_background = None

        # Create assets folder if it doesn't exist
        Path(assets_folder).mkdir(exist_ok=True)
        Path(os.path.join(assets_folder, "characters")).mkdir(exist_ok=True)
        Path(os.path.join(assets_folder, "backgrounds")).mkdir(exist_ok=True)
        Path(os.path.join(assets_folder, "animations")).mkdir(exist_ok=True)

    def load_image(self, filepath):
        """Load a PNG image"""
        try:
            image = pygame.image.load(filepath)
            return image
        except pygame.error as e:
            print(f"Cannot load image: {filepath}")
            print(e)
            return None

    def load_animation_from_spritesheet(self, spritesheet_path, frame_width, frame_height, 
                                        columns, rows, frame_duration=100):
        """
        Load animation from a Piskel-exported spritesheet
        spritesheet_path: path to the spritesheet PNG
        frame_width, frame_height: size of each frame
        columns, rows: grid layout of frames
        frame_duration: milliseconds per frame
        """
        spritesheet = self.load_image(spritesheet_path)
        if not spritesheet:
            return None

        frames = []
        for row in range(rows):
            for col in range(columns):
                x = col * frame_width
                y = row * frame_height
                frame = spritesheet.subsurface((x, y, frame_width, frame_height))
                frame = frame.copy()
                frames.append(AnimationFrame(frame, frame_duration))

        return Animation(frames, loop=True)

    def load_animation_from_frames(self, frame_folder, frame_duration=100):
        """
        Load animation from individual frame images (Piskel exported as sequence)
        frame_folder: folder containing frame images (frame_0.png, frame_1.png, etc.)
        """
        frames = []
        frame_files = sorted([f for f in os.listdir(frame_folder) if f.endswith('.png')])

        for frame_file in frame_files:
            image = self.load_image(os.path.join(frame_folder, frame_file))
            if image:
                frames.append(AnimationFrame(image, frame_duration))

        if frames:
            return Animation(frames, loop=True)
        return None

    def add_character(self, char_name, idle_animation=None, idle_image=None, 
                     width=50, height=50):
        """Register a new character"""
        character = Character(char_name, idle_animation, idle_image, width, height)
        self.characters[char_name] = character
        if not self.current_character:
            self.current_character = character
        return character

    def add_background(self, bg_name, animation=None, static_image=None):
        """Register a new background"""
        background = Background(bg_name, animation, static_image)
        self.backgrounds[bg_name] = background
        if not self.current_background:
            self.current_background = background
        return background

    def switch_character(self, char_name):
        """Switch to a different character"""
        if char_name in self.characters:
            self.current_character = self.characters[char_name]
            self.current_character.set_animation('idle')
            return True
        return False

    def switch_background(self, bg_name):
        """Switch to a different background"""
        if bg_name in self.backgrounds:
            self.current_background = self.backgrounds[bg_name]
            return True
        return False

    def update(self, dt):
        """Update all sprites"""
        if self.current_character:
            self.current_character.update(dt)
        if self.current_background:
            self.current_background.update(dt)

    def draw(self, surface):
        """Draw background and character"""
        if self.current_background:
            self.current_background.draw(surface)
        if self.current_character:
            self.current_character.draw(surface)

    def get_character(self, char_name):
        """Get a character without switching"""
        return self.characters.get(char_name)

    def get_background(self, bg_name):
        """Get a background without switching"""
        return self.backgrounds.get(bg_name)

    def list_characters(self):
        """Return list of available characters"""
        return list(self.characters.keys())

    def list_backgrounds(self):
        """Return list of available backgrounds"""
        return list(self.backgrounds.keys())
