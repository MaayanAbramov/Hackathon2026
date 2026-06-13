from transformers import AutoProcessor, pipeline
from optimum.intel.openvino import OVModelForSpeechSeq2Seq

_pipeline = None

def _get_model(model_id="openai/whisper-base"):
    global _pipeline
    
    if _pipeline is None:
        print(f"\n[OpenVINO] Compiling and loading {model_id} to Intel NPU...")
        print("[OpenVINO] Note: The first run takes time to compile. Subsequent runs are instant.")
        
        # Load the Hugging Face processor
        processor = AutoProcessor.from_pretrained(model_id)
        
        # Export the model to OpenVINO format and target the NPU
        ov_model = OVModelForSpeechSeq2Seq.from_pretrained(
            model_id, 
            export=True, 
            device="NPU",
            compile=True
        )
        
        # Create the inference pipeline
        _pipeline = pipeline(
            "automatic-speech-recognition",
            model=ov_model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            device="NPU"
        )
        print("[OpenVINO] Model loaded successfully!\n")
        
    return _pipeline

def transcribe(audio_path: str, model_size: str = "openai/whisper-base") -> dict:
    """
    Transcribe an audio file to text using Intel NPU.
    """
    pipe = _get_model(model_size)
    
    # Configure it to transcribe in Hebrew
    generate_kwargs = {"task": "transcribe", "language": "he"}
    
    # The pipeline handles file reading and inference
    result = pipe(audio_path, generate_kwargs=generate_kwargs)
    
    return {
        "text": result["text"].strip(),
        "language": "he"
    }