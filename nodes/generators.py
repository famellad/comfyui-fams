import os
import sys
import folder_paths

# Adding the parent directory to the system path
# '..' represents the directory above the current file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our config file
try:
    from futils import *
    print("[INFO][Fam's] Successfully imported utils.")
except ImportError as e:
    print(f"[WARNING] Import failed: {e}")

node_path = os.path.dirname(os.path.realpath(__file__))
base_path = os.path.dirname(node_path)
tests_dir = os.path.join(base_path, "tests")
#t_booru_dir = os.path.join(tests_dir, "booru") 
folder_paths.folder_names_and_paths["booru"] = (
   [os.path.join(tests_dir, "booru")],
   {".txt"},
)

fam_log("debug", tests_dir)
print(sorted(folder_paths.get_filename_list("booru")))

# All tests
class BooruTests:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "test_name": [sorted(folder_paths.get_filename_list("booru"))],
                #"Stacked" : ("BOOLEAN", {"default": True}),
            }
        }

    # We output a standard ComfyUI text string
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE")
    FUNCTION = "load_text"
    CATEGORY = "Fams/Tests"

    def load_text(self, test_name):
        # Read and return the entire string payload
        try:
            with open(folder_paths.get_full_path("booru", test_name)) as f:
                pmp = ''.join(f.readlines()).split("########")
                positive = pmp[0]
                negative = pmp[1] 
            return (positive, negative)
        except Exception as e:
            return (f"Error reading file: {str(e)}",)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Forces ComfyUI to execute this node every single time 'Queue Prompt' is clicked.
        """
        # Return a unique value on every single check (e.g., a random float)
        return float("nan") # Or: return random.random()

# Main tests
class MainBooruTests:
    test_list = sorted(folder_paths.get_filename_list("booru"))

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Stacked"  : ("BOOLEAN", {"default": True}),
                "Monster"  : ("BOOLEAN", {"default": True}),
                "Puppy"    : ("BOOLEAN", {"default": True}),
                "Fountain" : ("BOOLEAN", {"default": True}),
                "Pound"    : ("BOOLEAN", {"default": False}),
                "Bedtime"  : ("BOOLEAN", {"default": False}),
                "Tongues"  : ("BOOLEAN", {"default": False}),
                "Teamwork" : ("BOOLEAN", {"default": False}),
            }
        }

    # We output a standard ComfyUI text string
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "queue_tests"
    CATEGORY = "Fams/Tests"

    def queue_tests(self, **kwargs):
        positive_list = []
        negative_list = []
        
        num_of_tests = 0

        for input_name, input_value in kwargs.items():
            if input_value:
                num_of_tests += 1
                fam_log("info", f"{input_name} test enabled. Queueing.")
                with open(folder_paths.get_full_path("booru", infer_full_filename(self.test_list, input_name))) as f:
                    pmp = ''.join(f.readlines()).split("########")
                    positive = pmp[0]
                    negative = pmp[1] 
                    positive_list.append(positive)
                    negative_list.append(negative)
            else:
                fam_log("info", f"{input_name} test disabled. Skipping.")

        if num_of_tests == 0:
            positive_list.append("A red circle in a sky with clouds background, inside the circle the words \"You need to select one, dumbass.\" can be read in big, bold white letters.")
            negative_list.append("1girl, 1boy, solo, face, human, person, ")

        return (positive_list, negative_list)
        # Read and return the entire string payload
        #try:
        #    with open(folder_paths.get_full_path("booru", test_name)) as f:
        #        pmp = ''.join(f.readlines()).split("########")
        #        positive = pmp[0]
        #        negative = pmp[1] 
        #    return (positive, negative)
        #except Exception as e:
        #    return (f"Error reading file: {str(e)}",)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Forces ComfyUI to execute this node every single time 'Queue Prompt' is clicked.
        """
        # Return a unique value on every single check (e.g., a random float)
        return float("nan") # Or: return random.random()