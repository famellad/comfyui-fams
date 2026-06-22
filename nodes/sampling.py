import sys
import os
import math
import nodes as n
import comfy.samplers as cs

# Adding the parent directory to the system path
# '..' represents the directory above the current file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our config file
try:
    from futils import *
    print("[INFO][Fam's] Successfully imported utils.")
except ImportError as e:
    print(f"[WARNING] Import failed: {e}")


class KSamplerComplex:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent_image": ("LATENT", ),

                "structure_model": ("MODEL", ),
                "structure_noise_seed" : ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "structure_steps": ("INT", {"default": 7, "min": 1, "max": 10000}),
                "structure_cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "structure_sampler_name": (cs.KSampler.SAMPLERS, ),
                "structure_scheduler": (cs.KSampler.SCHEDULERS, ),
                "structure_positive": ("CONDITIONING", ),
                "structure_negative": ("CONDITIONING", ),

                "style_noise_seed" : ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "style_steps": ("INT", {"default": 7, "min": 0, "max": 10000}),
                "style_cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "style_sampler_name": (cs.KSampler.SAMPLERS, ),
                "style_scheduler": (cs.KSampler.SCHEDULERS, ),

                "specifics_noise_seed" : ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "specifics_steps": ("INT", {"default": 7, "min": 0, "max": 10000}),
                "specifics_cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.05, "round": 0.01}),
                "specifics_sampler_name": (cs.KSampler.SAMPLERS, ),
                "specifics_scheduler": (cs.KSampler.SCHEDULERS, ),

                #"add_noise": (["enable", "disable"], {"advanced": True}),
                #"return_with_leftover_noise": (["disable", "enable"], {"advanced": True}),
                "share_seed": ("BOOLEAN", {"default": False, "tooltip": "Only use the seed defined in the Structure section."}),
                "share_cfg": ("BOOLEAN", {"default": False, "tooltip": "Only use the CFG value defined in the Structure section."}), 
                "share_sampler_name": ("BOOLEAN", {"default": False, "tooltip": "Only use the sampler defined in the Structure section."}),
                "share_scheduler": ("BOOLEAN", {"default": False, "tooltip": "Only use the scheduler defined in the Structure section."}),
                #"share_positive": ("BOOLEAN", {"default": True, }),
                #"share_negative": ("BOOLEAN", {"default": True, }),
                "generation_strategy": (["total_pass", "cumulative_pass", "individual_pass"], {"tooltip": ""}),
                "pass_overlap": ("INT", {"default": 0, "min": 0, "max": 5}),
                "preview_structure": ("BOOLEAN", {"default": False, "tooltip": "Only generate the structure pass, to get a preview of the composition and a sense of the colors."}),
                "low_res_hack": ("BOOLEAN", {"default": False, "advanced": True, "tooltip": "Some models produce better compositions with smaller latents, this shrinks the latent for the first pass to lock that smaller composition in, and then restores the original size for the rest of the generation."}),
                "lrh_factor": ("FLOAT", {"default": 0.7, "min": 0.05, "max": 0.95, "step": 0.05}),
                "hi_res_fix": ("BOOLEAN", {"default": False, "tooltip": "Increase the size of the latent mid-generation to ultimate generate a larger image with more detail."}),
                "hrf_factor": ("FLOAT", {"default": 1.5, "min": 1.0, "max": 8.0, "step": 0.1, "tooltip": "Higher values tend to overcook the image, pick more conservative sampler/scheduler pairs or lower the guidance for the latter passes."}),
                "hrf_method": (["double", "single_early", "single_late"], {"tooltip": "double: The latent is upscaled two times, once before the style pass and again before the specifics pass to reach the desired factor.\nsingle_early: The latent is upscaled only once, right before the style pass.\nsingle_late: The latent is upscaled only once, right before the specifics pass.",}),
            },
            "optional": {
                "style_model": ("MODEL", ),
                "style_positive": ("CONDITIONING", ),
                "style_negative": ("CONDITIONING", ),

                "specifics_model": ("MODEL", ),
                "specifics_positive": ("CONDITIONING", ),
                "specifics_negative": ("CONDITIONING", ),
            }
        }
    
    RETURN_TYPES = ("LATENT", "LATENT", "LATENT")
    RETURN_NAMES = ("FINAL_LATENT", "STYLIZED_LATENT", "STRUCTURAL_LATENT")

    FUNCTION = "sample_complex"

    CATEGORY = "Fams/Samplers"

    #def sample_complex(self, structure_model, structure_noise_seed, structure_steps, structure_cfg, structure_sampler_name, structure_scheduler, structure_positive, structure_negative, style_model, style_noise_seed, style_steps, style_cfg, style_sampler_name, style_scheduler, style_positive, style_negative, specifics_model, specifics_noise_seed, specifics_steps, specifics_cfg, specifics_sampler_name, specifics_scheduler, specifics_positive, specifics_negative, latent_image, add_noise, return_with_leftover_noise, share_seed, share_cfg, share_sampler_name, share_scheduler, share_positive, share_negative, preview_structure, low_res_hack, lrh_factor, hi_res_fix, hrf_factor):
    def sample_complex(self, structure_model, structure_noise_seed, structure_steps, structure_cfg, structure_sampler_name, structure_scheduler, structure_positive, structure_negative, style_noise_seed, style_steps, style_cfg, style_sampler_name, style_scheduler, specifics_noise_seed, specifics_steps, specifics_cfg, specifics_sampler_name, specifics_scheduler, latent_image, share_seed, share_cfg, share_sampler_name, share_scheduler, generation_strategy, pass_overlap, preview_structure, low_res_hack, lrh_factor, hi_res_fix, hrf_factor, hrf_method, style_model=0, style_positive=0, style_negative=0, specifics_model=0, specifics_positive=0, specifics_negative=0):
    #def sample_complex(self, **kwargs): # I ain't typing all that
        denoise=1.0
        add_noise=True
        return_with_leftover_noise=False

        sq_hrf_factor = round(math.sqrt(hrf_factor))

        orig_latent_width  = latent_image["samples"].shape[-1]
        orig_latent_height = latent_image["samples"].shape[-2]

        if share_seed:
            style_noise_seed = structure_noise_seed
            specifics_noise_seed = structure_noise_seed
        if share_cfg:
            style_cfg = structure_cfg
            specifics_cfg = structure_cfg
        if share_sampler_name:
            style_sampler_name = structure_sampler_name
            specifics_sampler_name = structure_sampler_name
        if share_scheduler:
            style_scheduler = structure_scheduler
            specifics_scheduler = structure_scheduler

        if style_model == 0:
            style_model = structure_model
        if specifics_model == 0:
            specifics_model = structure_model
        
        if style_positive == 0:
            style_positive = structure_positive
        if style_negative == 0:
            style_negative = structure_negative

        if specifics_positive == 0:
            specifics_positive = structure_positive
        if specifics_negative == 0:
            specifics_negative = structure_negative

        force_full_denoise = True
        if return_with_leftover_noise == "enable":
            force_full_denoise = False
        disable_noise = False
        if add_noise == "disable":
            disable_noise = True

        # TODO implement pass overlap, implement generation methods
        total_steps = structure_steps + style_steps + specifics_steps
        struc_total_step = total_steps
        style_total_step = total_steps
        specs_total_step = total_steps
        struc_start_step = 0
        style_start_step = structure_steps
        specs_start_step = structure_steps + style_steps

        if generation_strategy == "individual_pass":
            struc_total_step = structure_steps
            style_total_step = style_steps
            specs_total_step = specifics_steps
            struc_start_step = 0
            style_start_step = 0
            specs_start_step = 0
        elif generation_strategy == "hybrid_pass":
            struc_total_step = structure_steps
            style_total_step = structure_steps + style_steps
            specs_total_step = total_steps
            struc_start_step = 0
            style_start_step = struc_total_step
            specs_start_step = style_total_step

        # Leg 1
        if low_res_hack:
            #orig_latent_dims = {}
            latent_image = upscale_latent_by(latent_image, "bislerp", lrh_factor)

        latent_struc = n.common_ksampler(structure_model, structure_noise_seed, struc_total_step, structure_cfg, structure_sampler_name, structure_scheduler, structure_positive, structure_negative, latent_image, denoise=denoise, disable_noise=disable_noise, start_step=struc_start_step, last_step=structure_steps, force_full_denoise=force_full_denoise)[0]
        
        if preview_structure:
            return(latent_struc, latent_struc, latent_struc)
        
        if low_res_hack:
            latent_struc = upscale_latent(latent_struc, "bislerp", orig_latent_width, orig_latent_height)

        # Leg 2
        if hi_res_fix:
            if hrf_method == "single_early":
                latent_struc = upscale_latent_by(latent_struc, "bislerp", hrf_factor)
            elif hrf_method == "double":
                latent_struc = upscale_latent_by(latent_struc, "bislerp", sq_hrf_factor)

        if style_steps == 0:
            latent_style = latent_struc
        else:
            latent_style = n.common_ksampler(style_model, style_noise_seed, style_total_step, style_cfg, style_sampler_name, style_scheduler, style_positive, style_negative, latent_struc, denoise=denoise, disable_noise=disable_noise, start_step=style_start_step, last_step=structure_steps + style_steps, force_full_denoise=force_full_denoise)[0]
        
        # Leg 3
        if hi_res_fix:
            if hrf_method == "single_late":
                latent_struc = upscale_latent_by(latent_struc, "bislerp", hrf_factor)
            elif hrf_method == "double":
                latent_style = upscale_latent(latent_style, "bislerp", round(orig_latent_width * hrf_factor), round(orig_latent_height * hrf_factor))
    
        if specifics_steps == 0:
            return(latent_style, latent_style, latent_struc)

        latent_specs = n.common_ksampler(specifics_model, specifics_noise_seed, specs_total_step, specifics_cfg, specifics_sampler_name, specifics_scheduler, specifics_positive, specifics_negative, latent_style, denoise=denoise, disable_noise=disable_noise, start_step=specs_start_step, last_step=10000, force_full_denoise=force_full_denoise)[0]

        return (latent_specs, latent_style, latent_struc)