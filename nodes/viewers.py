class QueuePreviewer:
    @classmethod
    def INPUT_TYPES(s):
        # Absolutely empty inputs
        return {"required": {}}

    # No outputs either! We're JS hacking this one all the way, babey!
    RETURN_TYPES = ()
    FUNCTION = "do_nothing"
    CATEGORY = "Fams/Viewers"
    
    # OUTPUT_NODE = True tells ComfyUI not to prune this node 
    # even though it doesn't connect to anything.
    OUTPUT_NODE = True 

    def do_nothing(self):
        # This function will never actually be called, 
        # but ComfyUI requires it to exist.
        return ()