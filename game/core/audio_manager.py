"""Audio manager for music, sound effects, and voice clips."""
import pygame
import os
import numpy as np
from pygame import sndarray


class AudioManager:
    """Manages all audio playback including music, SFX, and voice clips."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one audio manager exists."""
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the audio manager."""
        if self._initialized:
            return

        self._initialized = True

        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Master volume boost - multiplies audio amplitude beyond pygame's 1.0 limit
        # Values > 1.0 will make audio louder (e.g., 2.0 = 2x louder)
        self.MASTER_VOLUME_BOOST = 2.5

        # Volume settings (0.0 to 1.0) - these are applied AFTER the boost
        self.music_volume = 0.2
        self.sfx_volume = 0.9
        self.voice_volume = 1.0

        # Per-clip volume adjustments (multipliers applied during load)
        # Allows fine-tuning relative volume of specific files
        self.clip_adjustments = {
            # Music
            'music_title': 1.0,
            'music_cloud': 1.0,
            'music_jungle': 1.0,
            'music_water': 1.0,
            'music_VictoryMusic': 1.0,

            # SFX
            'sfx_choose': 1.0,
            'sfx_select': 1.0,
            'sfx_StartMission': 1.0,
            'sfx_VideoPopup': 1.0,
            'sfx_MissionComplete': 1.0,
            'sfx_rep': 1.0,

            # Voice
            'voice_Clap': 1.0,
            'voice_Complete': 1.0,
            'voice_LateralArm': 1.0,
            'voice_LateralHip': 1.0,
            'voice_LateralLunge': 1.0,
            'voice_MissionSelect': 1.0,
            'voice_ParallelArm': 1.0,
            'voice_RightBend': 1.0,
            'voice_RightLunge': 1.0,
            'voice_Squat': 1.0,
            'voice_ToeTouch': 1.0,
            'voice_Welcome': 1.0
        }

        # Current music track
        self.current_music = None

        # Preload all audio files
        self.music = {}
        self.sfx = {}
        self.voice = {}

        self._load_audio()

    def _load_audio(self):
        """Load all audio files into memory."""
        print("Loading audio files...")

        # Load music tracks
        music_files = {
            'title': 'game/data/music/title.mp3',
            'cloud': 'game/data/music/cloud.mp3',
            'jungle': 'game/data/music/jungle.mp3',
            'water': 'game/data/music/water.mp3',
            'victory': 'game/data/music/VictoryMusic.mp3'
        }

        for name, path in music_files.items():
            if os.path.exists(path):
                self.music[name] = path
                print(f"  Loaded music: {name}")
            else:
                print(f"  Warning: Music file not found: {path}")

        # Load sound effects
        sfx_files = {
            'choose': 'game/data/sfx/sfx_choose.mp3',
            'select': 'game/data/sfx/sfx_select.mp3',
            'start_mission': 'game/data/sfx/sfx_StartMission.mp3',
            'video_popup': 'game/data/sfx/sfx_VideoPopup.mp3',
            'mission_complete': 'game/data/sfx/sfx_MissionComplete.mp3',
            'rep': 'game/data/sfx/sfx_rep.mp3'
        }

        for name, path in sfx_files.items():
            if os.path.exists(path):
                try:
                    # Load and boost the sound
                    sound = self._load_and_boost_sound(path)
                    if sound:
                        self.sfx[name] = sound
                        self.sfx[name].set_volume(self.sfx_volume)
                        print(f"  Loaded SFX: {name}")
                except Exception as e:
                    print(f"  Error loading SFX {name}: {e}")
            else:
                print(f"  Warning: SFX file not found: {path}")

        # Load voice clips
        voice_files = {
            'welcome': 'game/data/voice/Welcome.wav',
            'mission_select': 'game/data/voice/MissionSelect.wav',
            'complete': 'game/data/voice/Complete.wav',
            'clap': 'game/data/voice/Clap.wav',
            'lateral_arm': 'game/data/voice/LateralArm.wav',
            'lateral_hip': 'game/data/voice/LateralHip.wav',
            'lateral_lunge': 'game/data/voice/LateralLunge.wav',
            'parallel_arm': 'game/data/voice/ParallelArm.wav',
            'right_bend': 'game/data/voice/RightBend.wav',
            'right_lunge': 'game/data/voice/RightLunge.wav',
            'squat': 'game/data/voice/Squat.wav',
            'toe_touch': 'game/data/voice/ToeTouch.wav'
        }

        for name, path in voice_files.items():
            if os.path.exists(path):
                try:
                    # Load and boost the sound
                    sound = self._load_and_boost_sound(path)
                    if sound:
                        self.voice[name] = sound
                        self.voice[name].set_volume(self.voice_volume)
                        print(f"  Loaded voice: {name}")
                except Exception as e:
                    print(f"  Error loading voice {name}: {e}")
            else:
                print(f"  Warning: Voice file not found: {path}")

        print("Audio loading complete!")

    def _load_and_boost_sound(self, path):
        """
        Load a sound file and apply volume boost by amplifying the audio data.

        Args:
            path: Path to the audio file

        Returns:
            pygame.mixer.Sound object with boosted volume, or None if failed
        """
        try:
            # Load the original sound
            original_sound = pygame.mixer.Sound(path)

            # Get the audio array
            sound_array = sndarray.array(original_sound)

            # Check for per-clip adjustment
            # Extract filename without extension for lookup
            filename = os.path.splitext(os.path.basename(path))[0]
            # Check for matches like 'sfx_rep' or 'voice_Squat' or just 'Squat'
            # Look in folders to determine prefix
            prefix = ""
            if "sfx" in path: prefix = "sfx_"
            elif "voice" in path: prefix = "voice_"
            elif "music" in path: prefix = "music_"

            clip_boost = self.clip_adjustments.get(prefix + filename, 1.0)

            # Apply volume boost - multiply samples by boost factor
            # Clip to prevent overflow (int16 range is -32768 to 32767)
            boosted_array = np.clip(
                sound_array.astype(np.float32) * self.MASTER_VOLUME_BOOST * clip_boost,
                -32768, 32767
            ).astype(np.int16)

            # Create new sound from boosted array
            boosted_sound = sndarray.make_sound(boosted_array)

            return boosted_sound
        except Exception as e:
            print(f"  Warning: Could not boost {path}, using original: {e}")
            # Fallback to original sound without boost
            try:
                return pygame.mixer.Sound(path)
            except:
                return None

    def play_music(self, track_name, loops=-1, fade_ms=1000):
        """
        Play a music track with looping.

        Args:
            track_name: Name of the music track ('title', 'cloud', 'jungle', 'water', 'victory')
            loops: Number of times to loop (-1 for infinite)
            fade_ms: Fade in duration in milliseconds
        """
        if track_name == self.current_music and pygame.mixer.music.get_busy():
            return  # Already playing this track

        if track_name not in self.music:
            print(f"Warning: Music track '{track_name}' not found")
            return

        try:
            path = self.music[track_name]
            pygame.mixer.music.load(path)

            # Extract filename for clip adjustment
            filename = os.path.splitext(os.path.basename(path))[0]
            clip_boost = self.clip_adjustments.get("music_" + filename, 1.0)

            # Apply volume boost to music as well (clamped to 1.0 max for music)
            boosted_volume = min(self.music_volume * self.MASTER_VOLUME_BOOST * clip_boost, 1.0)
            pygame.mixer.music.set_volume(boosted_volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self.current_music = track_name
            print(f"Playing music: {track_name}")
        except Exception as e:
            print(f"Error playing music {track_name}: {e}")

    def stop_music(self, fade_ms=1000):
        """
        Stop the currently playing music.

        Args:
            fade_ms: Fade out duration in milliseconds
        """
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
            self.current_music = None

    def pause_music(self):
        """Pause the currently playing music."""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Unpause the music."""
        pygame.mixer.music.unpause()

    def play_sfx(self, sfx_name):
        """
        Play a sound effect.

        Args:
            sfx_name: Name of the sound effect ('choose', 'select', 'start_mission', etc.)
        """
        if sfx_name in self.sfx:
            try:
                self.sfx[sfx_name].play()
            except Exception as e:
                print(f"Error playing SFX {sfx_name}: {e}")
        else:
            print(f"Warning: SFX '{sfx_name}' not found")

    def play_voice(self, voice_name):
        """
        Play a voice clip.

        Args:
            voice_name: Name of the voice clip ('welcome', 'mission_select', 'complete', or exercise names)
        """
        if voice_name in self.voice:
            try:
                self.voice[voice_name].play()
            except Exception as e:
                print(f"Error playing voice {voice_name}: {e}")
        else:
            print(f"Warning: Voice clip '{voice_name}' not found")

    def play_exercise_voice(self, exercise_name):
        """
        Play voice clip for an exercise based on its name.

        Args:
            exercise_name: Exercise name from the exercise data (e.g., 'clap', 'lateral_raise')
        """
        # Map exercise names to voice clip names
        exercise_voice_map = {
            'clap': 'clap',
            'lateral_raise': 'lateral_arm',
            'lateral_hip_thrust': 'lateral_hip',
            'lateral_lunge': 'lateral_lunge',
            'parallel_arm_raise': 'parallel_arm',
            'right_side_bend': 'right_bend',
            'right_lunge': 'right_lunge',
            'squat_rep': 'squat',
            'toe_touch': 'toe_touch'
        }

        voice_name = exercise_voice_map.get(exercise_name.lower())
        if voice_name:
            self.play_voice(voice_name)
        else:
            print(f"Warning: No voice mapping for exercise '{exercise_name}'")

    def set_music_volume(self, volume):
        """
        Set music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        """
        Set sound effects volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sfx.values():
            sound.set_volume(self.sfx_volume)

    def set_voice_volume(self, volume):
        """
        Set voice clips volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.voice_volume = max(0.0, min(1.0, volume))
        for sound in self.voice.values():
            sound.set_volume(self.voice_volume)

    def get_music_for_category(self, category):
        """
        Get the appropriate music track name for an exercise category.

        Args:
            category: Exercise category ('arms', 'legs', 'torso')

        Returns:
            Music track name
        """
        category_music_map = {
            'legs': 'cloud',
            'arms': 'jungle',
            'torso': 'water'
        }
        return category_music_map.get(category, 'title')


# Global audio manager instance
_audio_manager = None


def get_audio_manager():
    """Get the global audio manager instance."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
