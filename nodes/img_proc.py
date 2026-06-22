import numpy as np
import torch
from wand.image import Image

import sys
import os
# Adding the parent directory to the system path
# '..' represents the directory above the current file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our config file
try:
    import futils as u
    print("[INFO][Fam's] Successfully imported utils.")
except ImportError as e:
    print(f"[WARNING] Import failed: {e}")

# Magicks
class MagickSelectiveBlur:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the inputs your node expects. 
        'required' inputs must be connected. 'optional' can be left blank.
        """
        return {
            "required": {
                "image" : ("IMAGE", ),
                "radius": ("FLOAT", {
                    "default": 15.0, 
                    "min": 0.0, 
                    "max": 2000.0, 
                    "step": 0.2,
                    }),
                "sigma": ("FLOAT", {
                    "default": 8.0, 
                    "min": 0.0, 
                    "max": 2000.0, 
                    "step": 0.2,
                    }),
                "threshold": ("FLOAT", {
                    "default": 0.25, 
                    "min": 0.0, 
                    "max": 1.0, 
                    "step": 0.001,
                    }),
            },
        }

    # The data types returned by the node (must match the execution method's return tuple)
    RETURN_TYPES = ("IMAGE", )
    
    # The names of the output slots on the UI
    RETURN_NAMES = ("PROCESSED_IMAGE", )

    # The name of the Python method that handles the actual logic
    FUNCTION = "process"

    # Where this node lives in the right-click menu hierarchy
    CATEGORY = "Fams/Image Processing"

    def process(self, image, radius, sigma, threshold):
            # image comes from ComfyUI as 4D: [B, H, W, C]
            output_images = []
            
            for img_tensor in image:
                # # 1. img_tensor is a clean 3D tensor: [H, W, C]
                # img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)

                # # 2. Import into Wand using the safe array importer
                # with Image.from_array(img_np) as img:
                #     img.type = 'truecolor'

                #     # 3. Apply your selective blur processing
                #     img.selective_blur(radius, sigma, threshold * img.quantum_range)

                #     # 4. Safely export raw pixels as a flat list of characters (0-255)
                #     # This completely bypasses the "array element with a sequence" bug
                #     pixel_data = img.export_pixels(0, 0, img.width, img.height, "RGB", "char")

                #     # 5. Load into a flat numpy array and reshape to 3D: (Height, Width, 3)
                #     out_np = np.array(pixel_data, dtype=np.uint8).reshape((img.height, img.width, 3))

                # # 6. Convert this individual image back to a float32 PyTorch tensor
                # proc_tensor = torch.from_numpy(out_np.astype(np.float32) / 255.0)
                # output_images.append(proc_tensor)
                with u.tensor_to_magick(img_tensor) as img:
                    img.selective_blur(radius, sigma, threshold * img.quantum_range)
                    proc_tensor = u.magick_to_tensor(img)

                output_images.append(proc_tensor)
            

            # 7. Stack all processed batch images back into a 4D tensor: [B, H, W, C]
            final_output = torch.stack(output_images, dim=0)

            return (final_output, )

class SimpleDepthOfField:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the inputs your node expects. 
        'required' inputs must be connected. 'optional' can be left blank.
        """
        return {
            "required": {
                "image" : ("IMAGE", ),
                "depth_map" : ("IMAGE", ),
                "focal_point": ("FLOAT", {
                    "default": 0.5, 
                    "min": 0.0, 
                    "max": 1.0, 
                    "step": 0.01,
                    }),
                "focal_range": ("FLOAT", {
                    "default": 0.1, 
                    "min": 0.0, 
                    "max": 1.0, 
                    "step": 0.01,
                    }),
                "max_blur": ("INT", {
                    "default": 15, 
                    "min": 1, 
                    "max": 255, 
                    "step": 2,
                    }),
            },
        }

    # The data types returned by the node (must match the execution method's return tuple)
    RETURN_TYPES = ("IMAGE", )
    
    # The names of the output slots on the UI
    RETURN_NAMES = ("PROCESSED_IMAGE", )

    # The name of the Python method that handles the actual logic
    FUNCTION = "apply_blur_pyramid_dof"

    # Where this node lives in the right-click menu hierarchy
    CATEGORY = "Fams/Image Processing"

    def _blur(self, img, kernel_size):
        """Helper to apply a high-quality, fast separable 1D Gaussian Blur"""
        if kernel_size <= 1:
            return img
        if kernel_size % 2 == 0:
            kernel_size += 1
            
        channels = img.shape[1]
        sigma = kernel_size / 3.0  # Standard bell-curve scaling
        
        # Create 1D Gaussian coordinate space
        x = torch.arange(kernel_size, device=img.device) - (kernel_size - 1) / 2
        kernel_1d = torch.exp(-x**2 / (2 * sigma**2))
        kernel_1d = kernel_1d / kernel_1d.sum()
        
        # Reshape kernels for 1D horizontal and vertical convolutions
        kernel_h = kernel_1d.view(1, 1, 1, kernel_size).repeat(channels, 1, 1, 1)
        kernel_v = kernel_1d.view(1, 1, kernel_size, 1).repeat(channels, 1, 1, 1)
        
        # Horizontal Pass
        padded = F.pad(img, [kernel_size // 2, kernel_size // 2, 0, 0], mode='reflect')
        img_h = F.conv2d(padded, kernel_h, groups=channels)
        
        # Vertical Pass
        padded_h = F.pad(img_h, [0, 0, kernel_size // 2, kernel_size // 2], mode='reflect')
        return F.conv2d(padded_h, kernel_v, groups=channels)

    def apply_blur_pyramid_dof(self, image, depth_map, focal_point, focal_range, max_blur):
        # Permute ComfyUI layout [B, H, W, C] -> Torch standard [B, C, H, W]
        img = image.permute(0, 3, 1, 2)
        depth = depth_map.permute(0, 3, 1, 2)[:, :1, :, :] # Extract 1 grayscale channel

        # 1. Calculate continuous Circle of Confusion (CoC) from 0.0 to 1.0
        coc = torch.abs(depth - focal_point)
        coc = torch.clamp(coc - (focal_range / 2.0), 0.0, 1.0)
        coc = coc / (1.0 - (focal_range / 2.0) + 1e-6)
        coc = torch.clamp(coc, 0.0, 1.0)

        # 2. Set up our Blur Pyramid levels (6 levels is the sweet spot for perfectly smooth gradients)
        num_levels = 6
        scaled_coc = coc * (num_levels - 1) # Scales 0.0 to 5.0
        
        blur_levels = []
        for i in range(num_levels):
            fraction = i / (num_levels - 1)
            current_kernel_size = int(fraction * max_blur)
            blur_levels.append(self._blur(img, current_kernel_size))

        # 3. Vectorized Piecewise Linear Interpolation across the pyramid
        # Every pixel calculates its proximity weight to each discrete blur level
        composited = torch.zeros_like(img)
        for i in range(num_levels):
            # Triangle function filter to isolate adjacent levels smoothly
            weight = torch.clamp(1.0 - torch.abs(scaled_coc - i), 0.0, 1.0)
            composited += blur_levels[i] * weight

        # 4. Turn it back into ComfyUI layout [B, H, W, C]
        output = composited.permute(0, 2, 3, 1)
        return (output,)
