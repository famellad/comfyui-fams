import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js"; // This is ComfyUI's websocket manager

app.registerExtension({
    name: "Fams.QueuePreviewer",
    
    // 1. Setup the Node UI
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "QueuePreviewer") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);
                
                this.previewImage = new Image();
                this.size = [400, 400]; // Default size
                this.resizable = true;  // Allows you to drag the bottom right corner!
            };

            // Re-using our bulletproof aspect-ratio math
            nodeType.prototype.onDrawBackground = function (ctx) {
                if (this.previewImage && this.previewImage.complete && this.previewImage.naturalWidth !== 0) {
                    const margin = 10;
                    
                    // The drawing area is the whole node minus margins and the title bar (~30px)
                    const title_height = LiteGraph.NODE_TITLE_HEIGHT;
                    const max_width = this.size[0] - (margin * 2);
                    const max_height = this.size[1] - title_height - (margin * 2);

                    const image_ratio = this.previewImage.naturalWidth / this.previewImage.naturalHeight;
                    const boundary_ratio = max_width / max_height;

                    let img_w = max_width;
                    let img_h = max_height;

                    if (image_ratio > boundary_ratio) {
                        img_w = max_width;
                        img_h = max_width / image_ratio;
                    } else {
                        img_h = max_height;
                        img_w = max_height * image_ratio;
                    }

                    const img_x = margin + (max_width - img_w) / 2;
                    const img_y = title_height + margin + (max_height - img_h) / 2;

                    ctx.save();
                    
                    // Draw a subtle border frame
                    ctx.strokeStyle = "#333";
                    ctx.lineWidth = 2;
                    ctx.strokeRect(img_x, img_y, img_w, img_h);
                    
                    // Paint the live frame!
                    ctx.drawImage(this.previewImage, img_x, img_y, img_w, img_h);
                    ctx.restore();
                } else {
                    // Idle state text
                    ctx.fillStyle = "#555";
                    ctx.font = "14px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText("Waiting for generation...", this.size[0] / 2, this.size[1] / 2);
                }
            };
        }
    },

    // 2. Setup the Global WebSocket Listener
    async setup() {
        // This listens to ComfyUI's internal binary preview stream
        api.addEventListener("b_preview", (event) => {
            // event.detail contains the raw binary image blob from the server
            const blob = event.detail;
            if (!blob) return;

            // Convert the binary blob into a temporary browser URL
            const url = URL.createObjectURL(blob);

            // Find all QueuePreviewer nodes on the canvas
            const nodes = app.graph.findNodesByType("QueuePreviewer");
            
            for (const node of nodes) {
                const tmpImage = new Image();
                // Create a temporary image
                tmpImage.onload = () => {
                    // Revoke the old url once the new one is in
                    if (node.previewImage && node.previewImage.src && node.previewImage.src.startsWith("blob:")) {
                        URL.revokeObjectURL(node.previewImage.src);
                    }

                    // Update with the fully cooked image
                    node.previewImage = tmpImage;

                    // Redraw the node
                    node.setDirtyCanvas(true, true);
                }
                
                // Load blob into hidden image
                tmpImage.src = url;
            }
        });

        // Clear the last frame
        api.addEventListener("status", (event) => {
            // Safe fallback checking both old and new API payload schemas
            const execInfo = event.detail?.status?.exec_info || event.detail?.exec_info;
            const queue_remaining = execInfo?.queue_remaining;
            
            // Debugging log to confirm the exact number in your console
            console.log("Current Queue Remaining:", queue_remaining);  

            // If queue_remaining is 0, we're done here
            if (queue_remaining === 0) {
                console.log("dbg2");
                const nodes = app.graph.findNodesByType("QueuePreviewer");

                for (const node of nodes) {
                    console.log("dbg3");
                    if (node.previewImage) {
                        console.log("dbg4");
                        // Pack it up, boys
                        if (node.previewImage.src && node.previewImage.src.startsWith("blob:")) {
                            URL.revokeObjectURL(node.previewImage.src);
                        }

                        // Uninstantiate
                        node.previewImage = new Image();

                        // Force redraw
                        node.setDirtyCanvas(true, true);
                    }
                }
            }
        });
    }
});