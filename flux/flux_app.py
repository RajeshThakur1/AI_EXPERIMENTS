import torch
from diffusers import FluxPipeline
import diffusers
from PIL import Image
import gradio as gr
import base64

_flux_rope = diffusers.models.transformers.transformer_flux.rope
def new_flux_rope(pos: torch.Tensor, dim: int, theta: int) -> torch.Tensor:
    assert dim % 2 == 0, "The dimension must be even."
    if pos.device.type == "cuda":
        return _flux_rope(pos.to("cpu"), dim, theta).to(device=pos.device)
    else:
        return _flux_rope(pos, dim, theta)
diffusers.models.transformers.transformer_flux.rope = new_flux_rope


pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    revision='refs/pr/1',
    torch_dtype=torch.bfloat16
).to("cuda")


def generate_image(prompt):
    # Generate the image
    out = pipe(
        prompt=prompt,
        guidance_scale=0.,
        height=1024,
        width=1024,
        num_inference_steps=4,
        max_sequence_length=256,
    ).images[0]
    
    return out

iface = gr.Interface(
    fn=generate_image,
    inputs = gr.Textbox(lines= 2, placeholder="Enter your prompt here ...."),
    outputs = gr.Image(type="pil"),
    title="FLUX Image Generator",
    description= "Enter a prompt to generate an image using fluc.1-scnell model."
)

iface.launch(share=True)