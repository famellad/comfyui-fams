import { app } from "../../scripts/app.js"

function addSectionHeader(node, targetWidgetName, headerText, rectColor, textColor, numWidgets) {
    const targetIndex = node.widgets?.findIndex(w => w.name === targetWidgetName);
    if (targetIndex === -1 || targetIndex === undefined) return;

    // Prevent duplicates
    const headerName = `header_${targetWidgetName}`;
    if (node.widgets[targetIndex - 1]?.name === headerName) return;

    const headerHeight = 36;

    // Make a header widget
    const headerWidget = {
        type: "custom_header",
        name: headerName,
        value: headerText,
        options: {},

        draw: function(ctx, node, widget_width, y, widget_height) {
            ctx.save();

            ctx.fillStyle = rectColor;
            ctx.fillRect(0, y + 8, widget_width, headerHeight - 14);

            ctx.fillStyle = textColor;
            ctx.font = "bolder 14px sans-serif";
            ctx.textBaseline = "middle";
            ctx.fillText(this.value, 10, y + 10 + (headerHeight - 16) / 2);

            ctx.restore();
        },

        computeSize: function() {
            return [0, headerHeight];
        },

        // Do nothing
        mouse: function() {
            return true;
        }
    };

    // Inject the header
    node.widgets.splice(targetIndex, 0, headerWidget);

    // Recalculate node size
    if (node.computeSize) {
        node.setSize(node.computeSize());
    }
    
}

app.registerExtension({
    name: "Fams.KSamplerComplexHeaders",
    async nodeCreated(node) {
        addSectionHeader(node, "structure_noise_seed", "  > Structure", "#322a23", "#f6a156");
        addSectionHeader(node, "style_noise_seed", "  > Style", "#2b3223", "#b3f656");
        addSectionHeader(node, "specifics_noise_seed", "  > Specifics",  "#232a32", "#56b9f6");
        addSectionHeader(node, "share_seed", "  > Extra Parameters", "#322329", "#f2819f");
    }
});