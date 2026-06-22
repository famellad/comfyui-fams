#import os
#import sys
import numpy as np
from wand.image import Image
import torch
import comfy.utils

debug = True

def strengthify (text, strength):
    return "(" + text + ":" + str(strength) + ")"

def strengthify_aam (text, strength):
    return "::" + text + "::" + str(strength)

def sanitize_for_prompt(text):
    return text.lower().replace("(", "\\(").replace(")", "\\)")

def tensor_to_magick(img_tensor):
    img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
    img_magick = Image.from_array(img_np)
    img_magick.type = 'truecolor'

    return img_magick

def magick_to_tensor(img_magick):
    pixel_data = img_magick.export_pixels(0, 0, img_magick.width, img_magick.height, "RGB", "char")
    out_np = np.array(pixel_data, dtype=np.uint8).reshape((img_magick.height, img_magick.width, 3))
    img_tensor = torch.from_numpy(out_np.astype(np.float32) / 255.0)

    return img_tensor

def infer_full_filename(file_list, partial):
    for f in file_list:
        if partial in f:
            fam_log("debug", f"Filename found: {f}")
            return f

def fam_log(level, text):
    if debug == False and level == "debug":
        return
    # lvl_dict = {
    #     "debug"  : "[DEBUG] ",
    #     "info"   : "[INFO]  ",
    #     "warn"   : "[WARN]  ",
    #     "error"  : "[ERROR] ",
    # }
    lvl_dict = {
        "debug"  : "[🪲] ",
        "info"   : "[ℹ️] ",
        "warn"   : "[⚠️] ",
        "error"  : "[🛑] ",
    }

    fam_str = "[Fam's] "

    final_str = lvl_dict[level] + fam_str + text

    print(final_str)

def upscale_latent_by(samples, upscale_method, scale_by):
    s = samples.copy()
    width = round(samples["samples"].shape[-1] * scale_by)
    height = round(samples["samples"].shape[-2] * scale_by)
    s["samples"] = comfy.utils.common_upscale(samples["samples"], width, height, upscale_method, "disabled")
    return s

def upscale_latent(samples, upscale_method, width, height):
    s = samples.copy()
    s["samples"] = comfy.utils.common_upscale(samples["samples"], width, height, upscale_method, "disabled")
    return s