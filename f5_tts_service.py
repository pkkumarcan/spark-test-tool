"""
F5-TTS Service Implementation
Streamlined service for practical text-to-speech synthesis
"""

import os
import asyncio
import logging
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import torch
import torchaudio
import numpy as np

# Import F5-TTS components
try:
    from f5_tts.api import F5TTS
    from f5_tts.model import DiT, UNetT
    from f5_tts.infer.utils_infer import (
        load_model,
        preprocess_ref_audio_text,
        infer_process,
        save_spectrogram
    )
except ImportError as e:
    logging.error(f"F5-TTS import failed: {e}")
    logging.info("Installing F5-TTS...")
    os.system("pip install git+https://github.com/SWivid/F5-TTS.git")
    from f5_tts.api import F5TTS

logger = logging.getLogger(__name__)

class F5TTSService:
    """Streamlined F5-TTS service for practical synthesis"""
    
    def __init__(self):
        self.model = None
        self.vocoder = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 24000
        # Use a dedicated persistent storage path for data
        persistent_storage_path = Path("/workspace")
        self.output_dir = persistent_storage_path.joinpath("output")
        self.voices_dir = persistent_storage_path.joinpath("voices")
        self.checkpoints_dir = persistent_storage_path.joinpath("checkpoints")
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.voices_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        self.ready = False
        self.available_voices = {}
        
        logger.info(f"F5TTSService initialized on device: {self.device}")
    
    async def initialize(self):
        """Initialize the F5-TTS model"""
        try:
            logger.info("Loading F5-TTS model...")
            
            # Initialize F5-TTS with automatic model downloading
            logger.info("Initializing F5-TTS with automatic model loading...")
            # Use the local vocabulary file copied into the container
            vocab_path = "/app/app/assets/vocab.txt"

            self.model = F5TTS(
                ckpt_file=None,  # Let F5-TTS handle model downloading
                vocab_file=vocab_path,
                ode_method="euler",
                use_ema=True,
                device=self.device
            )
            
            # Load default voices from archive if available
            await self._load_default_voices()
            
            self.ready = True
            logger.info("F5-TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize F5-TTS: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return self.ready and self.model is not None
    
    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> str:
        """Synthesize speech from text"""
        if not self.is_ready():
            raise RuntimeError("TTS service not ready")
        
        try:
            # Get reference audio for voice cloning
            ref_audio_path, ref_text = await self._get_reference_audio(voice, language)
            
            # Generate unique output filename
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_filename = f"speech_{text_hash}_{language}.wav"
            output_path = self.output_dir / output_filename
            
            # Run synthesis
            logger.info(f"Generating speech for text: '{text[:50]}...'")
            
            # Use F5-TTS inference
            audio, sr, _ = self.model.infer(
                ref_file=ref_audio_path,
                ref_text=ref_text,
                gen_text=text,
                remove_silence=True,
                speed=speed
            )
            
            # Save audio
            if isinstance(audio, torch.Tensor):
                if audio.ndim == 1:
                    audio = audio.unsqueeze(0)
            elif isinstance(audio, np.ndarray):
                audio = torch.from_numpy(audio)
                if audio.ndim == 1:
                    audio = audio.unsqueeze(0)
            torchaudio.save(str(output_path), audio, self.sample_rate)
            
            logger.info(f"Speech generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise
    
    async def register_voice(self, audio_file, voice_name: str) -> str:
        """Register a new voice from uploaded audio"""
        try:
            # Save uploaded file
            voice_id = f"{voice_name}_{hashlib.md5(voice_name.encode()).hexdigest()[:8]}"
            voice_path = self.voices_dir / f"{voice_id}.wav"
            
            # Save file content
            content = await audio_file.read()
            with open(voice_path, "wb") as f:
                f.write(content)
            
            # Process audio for voice cloning
            processed_path = await self._process_voice_sample(voice_path)
            
            # Register voice
            self.available_voices[voice_id] = {
                "name": voice_name,
                "path": str(processed_path),
                "text": f"Hello, this is a sample of the {voice_name} voice."
            }
            
            logger.info(f"Voice registered: {voice_id}")
            return voice_id
            
        except Exception as e:
            logger.error(f"Voice registration failed: {e}")
            raise
    
    async def get_available_voices(self) -> List[Dict]:
        """Get list of available voices"""
        voices = []
        
        # Add default voices
        for voice_id, voice_data in self.available_voices.items():
            voices.append({
                "id": voice_id,
                "name": voice_data["name"],
                "type": "custom" if "custom" in voice_id else "default"
            })
        
        return voices
    
    async def _get_reference_audio(self, voice: Optional[str], language: str):
        """Get reference audio for voice cloning"""
        if voice and voice in self.available_voices:
            voice_data = self.available_voices[voice]
            return voice_data["path"], voice_data["text"]
        
        # Use default voice based on language
        default_voice = await self._get_default_voice(language)
        return default_voice["path"], default_voice["text"]
    
    async def _get_default_voice(self, language: str):
        """Get default voice for a language"""
        # Simple default voice mapping
        default_voices = {
            "en": {
                "path": str(self.voices_dir / "default_en.wav"),
                "text": "Hello, this is a sample of English speech."
            },
            "es": {
                "path": str(self.voices_dir / "default_es.wav"),
                "text": "Hola, esta es una muestra de habla en español."
            },
            "pt": {
                "path": str(self.voices_dir / "default_pt.wav"),
                "text": "Olá, esta é uma amostra de fala em português."
            },
            "de": {
                "path": str(self.voices_dir / "default_de.wav"),
                "text": "Hallo, das ist eine deutsche Sprachprobe."
            }
        }
        
        if language in default_voices:
            voice_info = default_voices[language]
            # Check if file exists, if not create a simple one
            if not Path(voice_info["path"]).exists():
                await self._create_default_voice(language, voice_info)
            return voice_info
        
        # Fallback to English
        return await self._get_default_voice("en")
    
    async def _create_default_voice(self, language: str, voice_info: dict):
        """Create a simple default voice file"""
        # Create a simple sine wave as placeholder
        duration = 3.0  # 3 seconds
        frequency = 440  # A4 note
        
        t = torch.linspace(0, duration, int(self.sample_rate * duration))
        audio = 0.3 * torch.sin(2 * np.pi * frequency * t)
        audio = audio.unsqueeze(0)  # Add channel dimension
        
        torchaudio.save(voice_info["path"], audio, self.sample_rate)
        logger.info(f"Created default voice for {language}")
    
    async def _process_voice_sample(self, voice_path: Path) -> Path:
        """Process uploaded voice sample"""
        try:
            # Load and resample to target sample rate
            audio, sr = torchaudio.load(voice_path)
            
            if sr != self.sample_rate:
                resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                audio = resampler(audio)
            
            # Convert to mono if stereo
            if audio.shape[0] > 1:
                audio = torch.mean(audio, dim=0, keepdim=True)
            
            # Normalize audio
            audio = audio / torch.max(torch.abs(audio))
            
            # Save processed audio
            processed_path = voice_path.with_suffix('.processed.wav')
            torchaudio.save(str(processed_path), audio, self.sample_rate)
            
            return processed_path
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return voice_path  # Return original if processing fails
    
    async def _load_default_voices(self):
        """Load any pre-existing voices from archive"""
        try:
            # Check if archive has default voices
            archive_voices = Path("/workspace/archive/testfiles")
            if archive_voices.exists():
                logger.info("Loading voices from archive...")
                # Copy any available voice samples
                for voice_file in archive_voices.glob("**/*.wav"):
                    if voice_file.stat().st_size > 1000:  # Skip very small files
                        lang_code = voice_file.parent.name.lower()
                        dest_path = self.voices_dir / f"default_{lang_code}.wav"
                        shutil.copy2(voice_file, dest_path)
                        
                        self.available_voices[f"default_{lang_code}"] = {
                            "name": f"Default {lang_code.upper()}",
                            "path": str(dest_path),
                            "text": f"Sample audio for {lang_code} language."
                        }
                        
                        logger.info(f"Loaded default voice for {lang_code}")
                        
        except Exception as e:
            logger.warning(f"Could not load archive voices: {e}")
            # Continue without archive voices
